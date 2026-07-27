"""
cavity_ray_tracing.py — Pure physics module for optical cavity ray tracing.

Owns:
    - CavityParameters: dataclass for cavity configuration.
    - CavityRayTracing: ABCD matrix ray tracing, mirror geometry, validation,
      stability analysis, and segment interpolation.
    - RAY_COLOR_DICT: module-level color palette for ray/figure theming.

Sign convention
---------------
    R < 0  ->  concave mirror
    R > 0  ->  convex mirror

Stability condition
-------------------
    g_i = 1 + L / R_i
    Stable iff  0 <= g1 * g2 <= 1
"""

import numpy as np

# ---------------------------------------------------------------------------
# Module-level color palette
# ---------------------------------------------------------------------------

RAY_COLOR_DICT: dict = {
    "red": {
        "ax_face": "#110000",
        "timer_bg": "#470000",
        "params_bg": "#FFB8B8",
        "plotly_rgb": "rgb(255, 60, 60)",
    },
    "blue": {
        "ax_face": "#00001A",
        "timer_bg": "#000047",
        "params_bg": "#B8B8FF",
        "plotly_rgb": "rgb(60, 120, 255)",
    },
    "green": {
        "ax_face": "#001100",
        "timer_bg": "#004700",
        "params_bg": "#B8FFB8",
        "plotly_rgb": "rgb(50, 220, 80)",
    },
    "orange": {
        "ax_face": "#090500",
        "timer_bg": "#471F00",
        "params_bg": "#FFD8B8",
        "plotly_rgb": "rgb(255, 150, 30)",
    },
    "purple": {
        "ax_face": "#0C000C",
        "timer_bg": "#470047",
        "params_bg": "#FFB8FF",
        "plotly_rgb": "rgb(180, 80, 255)",
    },
}


# ---------------------------------------------------------------------------
# CavityParameters — lightweight result container
# ---------------------------------------------------------------------------


class CavityParameters:
    """Simple class to store cavity configuration parameters."""

    def __init__(
        self,
        R1,
        R2,
        L,
        g1,
        g2,
        stability_product,
        is_stable,
        is_confocal,
        is_symmetric,
        mirror1_type,
        mirror2_type,
        cavity_config,
        mirror_description,
    ):
        self.R1 = R1
        self.R2 = R2
        self.L = L
        self.g1 = g1
        self.g2 = g2
        self.stability_product = stability_product
        self.is_stable = is_stable
        self.is_confocal = is_confocal
        self.is_symmetric = is_symmetric
        self.mirror1_type = mirror1_type
        self.mirror2_type = mirror2_type
        self.cavity_config = cavity_config
        self.mirror_description = mirror_description


# ---------------------------------------------------------------------------
# CavityRayTracing — pure physics core
# ---------------------------------------------------------------------------


class CavityRayTracing:
    """
    Core class for ray tracing in optical cavities with concave and/or convex mirrors.

    Provides:
    - Mirror geometry and intersection calculations for both concave (R < 0)
      and convex (R > 0) mirrors.
    - Ray transfer matrix (ABCD) operations.
    - Stability parameter calculation and analysis.
    - Parameter validation and error handling.
    - Segment interpolation for smooth animation frame generation.

    This class supports all cavity configurations:
    Concave-Concave, Convex-Convex, Concave-Convex, and Convex-Concave.
    """

    def __init__(self, R1=-80.0, R2=-80.0, L=70.0):
        """
        Initialize the cavity ray tracer.

        Parameters
        ----------
        R1 : float
            Radius of curvature for mirror 1 (negative for concave, positive for convex).
            Default: -80.0 cm
        R2 : float
            Radius of curvature for mirror 2 (negative for concave, positive for convex).
            Default: -80.0 cm
        L : float
            Cavity length (distance between mirror vertices).
            Default: 70.0 cm

        Notes
        -----
        - For concave mirrors, use negative R values (e.g., R1 = -80.0)
        - For convex mirrors, use positive R values (e.g., R1 = 80.0)
        - Stability requires: 0 <= g1*g2 <= 1, where g = 1 + L/R
        - Confocal condition: L = |R1| = |R2| (only for concave-concave cavities)

        Raises
        ------
        ValueError
            If parameters are invalid.
        """
        self._validate_cavity_parameters(R1, R2, L)
        self.R1 = R1
        self.R2 = R2
        self.L = L
        self._calculate_cavity_properties()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_cavity_parameters(self, R1, R2, L):
        """
        Validate cavity parameters.

        Parameters
        ----------
        R1, R2 : float
            Radii of curvature.
        L : float
            Cavity length.

        Raises
        ------
        ValueError
            If any parameter is invalid.
        TypeError
            If parameters are not numeric.
        """
        if not all(isinstance(x, (int, float)) for x in [R1, R2, L]):
            raise TypeError("R1, R2, and L must be numeric values")

        if R1 == 0:
            raise ValueError("R1 cannot be zero")
        if R2 == 0:
            raise ValueError("R2 cannot be zero")
        if L <= 0:
            raise ValueError("Cavity length L must be positive")

        if abs(R1) < L / 10:
            raise ValueError("R1 appears too small for the cavity length")
        if abs(R2) < L / 10:
            raise ValueError("R2 appears too small for the cavity length")

    def _validate_ray_parameters(self, y0_initial, theta0_initial_deg, N_round_trips):
        """
        Validate ray tracing parameters.

        Parameters
        ----------
        y0_initial : float
            Initial ray height.
        theta0_initial_deg : float
            Initial angle in degrees.
        N_round_trips : int
            Number of round trips.

        Raises
        ------
        ValueError
            If parameters are invalid.
        TypeError
            If parameters have wrong type.
        """
        if not isinstance(N_round_trips, int):
            raise TypeError("N_round_trips must be an integer")

        if N_round_trips < 1:
            raise ValueError("N_round_trips must be at least 1")

        if N_round_trips > 100:
            raise ValueError("N_round_trips too large (max 100)")

        if not isinstance(y0_initial, (int, float)):
            raise TypeError("y0_initial must be numeric")

        if not isinstance(theta0_initial_deg, (int, float)):
            raise TypeError("theta0_initial_deg must be numeric")

        if abs(y0_initial) > abs(self.R1) * 0.9:
            raise ValueError(f"Initial height too large (max {abs(self.R1) * 0.9:.1f})")

        if abs(theta0_initial_deg) > 45:
            raise ValueError("Initial angle too large (max ±45°)")

    # ------------------------------------------------------------------
    # Cavity properties
    # ------------------------------------------------------------------

    def _calculate_cavity_properties(self):
        """Calculate and store cavity properties (g-parameters, stability, etc.)."""
        self.g1 = 1 + self.L / self.R1
        self.g2 = 1 + self.L / self.R2
        self.stability_product = self.g1 * self.g2
        self.is_stable = 0 <= self.stability_product <= 1

        self.mirror1_type = "Concave" if self.R1 < 0 else "Convex"
        self.mirror2_type = "Concave" if self.R2 < 0 else "Convex"

        if self.R1 < 0 and self.R2 < 0:
            self.cavity_config = "Concave-Concave"
        elif self.R1 > 0 and self.R2 > 0:
            self.cavity_config = "Convex-Convex"
        elif self.R1 < 0 and self.R2 > 0:
            self.cavity_config = "Concave-Convex"
        else:
            self.cavity_config = "Convex-Concave"

        if self.mirror1_type == self.mirror2_type:
            self.mirror_description = f"{self.mirror1_type}"
        else:
            self.mirror_description = f"{self.mirror1_type}-{self.mirror2_type}"

        # Confocal: L == |R1| == |R2|, concave-concave only
        self.is_confocal = (
            self.R1 < 0
            and self.R2 < 0
            and abs(self.L - abs(self.R1)) < 1e-6
            and abs(abs(self.R1) - abs(self.R2)) < 1e-6
        )

        # Symmetric: identical radii (including sign)
        self.is_symmetric = abs(self.R1 - self.R2) < 1e-6

        # Mirror centers for plotting
        self.left_mirror_center_x = -self.L / 2 - self.R1
        self.right_mirror_center_x = self.L / 2 + self.R2

        # Focal points
        x_pole_L = -self.L / 2.0
        x_pole_R = self.L / 2.0
        self.F1x = x_pole_L - self.R1 * 0.5
        self.F2x = x_pole_R + self.R2 * 0.5

        # Centers of curvature
        self.C1x = self.left_mirror_center_x
        self.C2x = self.right_mirror_center_x

    def get_cavity_parameters(self) -> CavityParameters:
        """
        Get cavity parameters and stability information.

        Returns
        -------
        CavityParameters
            Object containing all cavity parameters.
        """
        return CavityParameters(
            R1=self.R1,
            R2=self.R2,
            L=self.L,
            g1=self.g1,
            g2=self.g2,
            stability_product=self.stability_product,
            is_stable=self.is_stable,
            is_confocal=self.is_confocal,
            is_symmetric=self.is_symmetric,
            mirror1_type=self.mirror1_type,
            mirror2_type=self.mirror2_type,
            cavity_config=self.cavity_config,
            mirror_description=self.mirror_description,
        )

    # ------------------------------------------------------------------
    # Mirror geometry helpers
    # ------------------------------------------------------------------

    def _get_x_on_mirror(self, y, R, center_x, side):
        """
        Calculate the x-coordinate on a spherical mirror for a given y.

        Parameters
        ----------
        y : float
            Y-coordinate.
        R : float
            Radius of curvature.
        center_x : float
            X-coordinate of mirror center.
        side : str
            'left' or 'right' indicating which mirror.

        Returns
        -------
        float
            X-coordinate on mirror surface, or np.nan if invalid.
        """
        if abs(y) > abs(R):
            return np.nan

        discriminant = R**2 - y**2
        if discriminant < 0:
            return np.nan

        if side == "left":
            return center_x + np.sign(R) * np.sqrt(discriminant)
        elif side == "right":
            return center_x - np.sign(R) * np.sqrt(discriminant)
        else:
            return np.nan

    def _get_mirror_arc_angles(self, arc_angle):
        """
        Return (theta1_left, theta2_left, theta1_right, theta2_right) in degrees
        for the left and right mirror arcs.

        This replicates the angle logic from the original _get_mirror_arcs but
        returns the raw angles so that plotting.py can sample them into Plotly
        Scatter traces (Plotly has no native Arc patch).
        """
        if self.R1 < 0:
            theta1_left, theta2_left = 180 - arc_angle, 180 + arc_angle
        else:
            theta1_left, theta2_left = -arc_angle, arc_angle

        if self.R2 < 0:
            theta1_right, theta2_right = -arc_angle, arc_angle
        else:
            theta1_right, theta2_right = 180 - arc_angle, 180 + arc_angle

        return theta1_left, theta2_left, theta1_right, theta2_right

    # ------------------------------------------------------------------
    # Ray tracing
    # ------------------------------------------------------------------

    def trace_ray(self, y0_initial=15.0, theta0_initial_deg=0.0, N_round_trips=2):
        """
        Perform ray tracing through the cavity using the ABCD matrix method.

        Parameters
        ----------
        y0_initial : float
            Initial height of ray from optical axis (cm).
        theta0_initial_deg : float
            Initial angle in degrees.
        N_round_trips : int
            Number of round trips to simulate.

        Returns
        -------
        ray_segments : list
            List of ray path segments; each segment is a list of (x, y) tuples.
        final_state : numpy.ndarray
            Final state vector [y, theta] after all round trips.

        Raises
        ------
        ValueError
            If ray parameters are invalid or ray escapes cavity.
        """
        self._validate_ray_parameters(y0_initial, theta0_initial_deg, N_round_trips)

        theta0_initial = np.deg2rad(theta0_initial_deg)

        # Transfer matrices
        M_prop = np.array([[1, self.L], [0, 1]])
        M_refl_1 = np.array([[1, 0], [2 / self.R1, 1]])
        M_refl_2 = np.array([[1, 0], [2 / self.R2, 1]])

        ray_segments = []
        current_segment = []

        y_theta_vec = np.array([[y0_initial], [theta0_initial]])

        # Initial point on Mirror 1
        x0 = self._get_x_on_mirror(
            y0_initial, self.R1, self.left_mirror_center_x, "left"
        )
        if np.isnan(x0):
            raise ValueError("Initial ray position is outside mirror aperture")

        current_segment.append((x0, y0_initial))

        for i in range(N_round_trips):
            # Propagation M1 → M2
            y_theta_vec = M_prop @ y_theta_vec
            y_at_M2 = y_theta_vec[0, 0]
            x_at_M2 = self._get_x_on_mirror(
                y_at_M2, self.R2, self.right_mirror_center_x, "right"
            )

            if np.isnan(x_at_M2):
                current_segment.append((self.L / 2, y_at_M2))
                ray_segments.append(current_segment.copy())
                break

            current_segment.append((x_at_M2, y_at_M2))
            ray_segments.append(current_segment.copy())
            current_segment = [(x_at_M2, y_at_M2)]

            # Reflection at M2
            y_theta_vec = M_refl_2 @ y_theta_vec

            # Propagation M2 → M1
            y_theta_vec = M_prop @ y_theta_vec
            y_at_M1 = y_theta_vec[0, 0]
            x_at_M1 = self._get_x_on_mirror(
                y_at_M1, self.R1, self.left_mirror_center_x, "left"
            )

            if np.isnan(x_at_M1):
                current_segment.append((-self.L / 2, y_at_M1))
                ray_segments.append(current_segment.copy())
                break

            current_segment.append((x_at_M1, y_at_M1))
            ray_segments.append(current_segment.copy())
            current_segment = [(x_at_M1, y_at_M1)]

            # Reflection at M1
            y_theta_vec = M_refl_1 @ y_theta_vec

        return ray_segments, y_theta_vec

    def trace_single_ray(
        self, y0_initial=15.0, theta0_initial_deg=0.0, N_round_trips=50
    ):
        """
        Trace a single ray through the cavity, returning a continuous path.

        Parameters
        ----------
        y0_initial : float
            Initial height of ray from optical axis (cm).
        theta0_initial_deg : float
            Initial angle in degrees.
        N_round_trips : int
            Number of round trips to simulate.

        Returns
        -------
        ray_path : list of tuples
            List of (x, y) coordinates along the full ray path.
        final_state : numpy.ndarray
            Final state vector [y, theta] after all round trips.
        """
        ray_segments, final_state = self.trace_ray(
            y0_initial, theta0_initial_deg, N_round_trips
        )

        ray_path = []
        for i, segment in enumerate(ray_segments):
            if i == 0:
                ray_path.extend(segment)
            else:
                ray_path.extend(segment[1:])

        return ray_path, final_state

    # ------------------------------------------------------------------
    # Interpolation (for animation frame generation)
    # ------------------------------------------------------------------

    def _interpolate_segments(self, segments, points_per_segment):
        """
        Interpolate ray segments for smooth animation.

        Parameters
        ----------
        segments : list
            List of ray path segments.
        points_per_segment : int
            Number of interpolation points per segment.

        Returns
        -------
        all_points : list
            List of (x, y) coordinates for all interpolated points.
        seg_ids : list
            Segment ID for each point.
        pt_idx_in_seg : list
            Point index within each segment.
        npps : int
            Actual number of points per segment used.
        """
        all_points = []
        seg_ids = []
        pt_idx_in_seg = []
        npps = int(max(2, points_per_segment))

        for s_idx, seg in enumerate(segments):
            if len(seg) < 2:
                continue
            (x0, y0), (x1, y1) = seg[0], seg[1]
            tvals = np.linspace(0.0, 1.0, npps)
            for j, t in enumerate(tvals):
                all_points.append((x0 + t * (x1 - x0), y0 + t * (y1 - y0)))
                seg_ids.append(s_idx)
                pt_idx_in_seg.append(j)

        return all_points, seg_ids, pt_idx_in_seg, npps
