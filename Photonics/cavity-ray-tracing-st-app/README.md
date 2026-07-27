<h1 align="center">
  🔬 Optical Cavity Ray Tracing
</h1>

<p align="center">
  <em>A modern, interactive Streamlit application for simulating and visualizing paraxial ray tracing within optical resonators using ABCD matrix formalism.</em>
</p>

<p align="center">
  <img alt="Python version" src="https://img.shields.io/badge/python-3.9%2B-blue">
  <img alt="Streamlit version" src="https://img.shields.io/badge/streamlit-1.35.0%2B-red">
  <img alt="Plotly version" src="https://img.shields.io/badge/plotly-5.22.0%2B-orange">
  <img alt="NumPy" src="https://img.shields.io/badge/numpy-1.26.0%2B-013243">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

<hr/>

## ✨ Features

- **Interactive Visualization:** Visualize paraxial rays bouncing between two spherical mirrors in real-time.
- **ABCD Matrix Formalism:** Built on robust optical physics for calculating ray propagation arrays.
- **Stability Analysis:** Automatically calculates cavity stability parameters ($g_1, g_2$) and visualizes them on a stability diagram.
- **Pre-configured Presets:** Quickly load standard configurations such as Confocal, Concentric, Hemispherical, or create your own asymmetric cavities.
- **Stunning Animations:** Generate smooth, animated Plotly figures tracing the path of the light rays.
- **Export Ready:** Export high-quality static figures (PNG) and dynamic animations (GIF/MP4) directly from the UI.
- **Customizable Themes:** Dynamic UI theming engine for dark, light, and colorful semantic styling.

---

## 🖼️ Gallery

Here are some sample outputs generated directly by the application:

### Concave-Concave Cavity
<p align="center">
  <img src="OUTPUTS/PLOTS/asymmetric_concave_concave_cavity_R1_-50.0_R2_-80.0_L_95.0_theta_1.0_rc_green_20260721_205857.png" alt="Asymmetric Concave-Concave Cavity" width="48%" />
  <img src="OUTPUTS/PLOTS/symmetric_concave_concave_cavity_R1_-50.0_R2_-50.0_L_80.0_theta_1.5_rc_blue_20260721_205857.png" alt="Symmetric Concave-Concave Cavity" width="48%" />
</p>

### Concave-Convex Cavity
<p align="center">
  <img src="OUTPUTS/PLOTS/asymmetric_concave_convex_cavity_R1_-100.0_R2_50.0_L_90.0_theta_0.0_rc_red_20260721_195953.png" alt="Concave-Convex Cavity 1" width="48%" />
  <img src="OUTPUTS/PLOTS/asymmetric_convex_concave_cavity_R1_60.0_R2_-120.0_L_115.0_theta_0.0_rc_green_20260721_195953.png" alt="Concave-Convex Cavity 2" width="48%" />
</p>

### Confocal Cavity (Stable)
<p align="center">
  <img
    src="OUTPUTS/PLOTS/confocal_cavity_R1_-80_R2_-80_L_80_theta_0.0_20260721_193108.png" 
    alt="Confocal Cavity" 
    width="75%" />
</p>

### Multi-Ray Bundle
<p align="center">
  <img
    src="OUTPUTS/PLOTS/cavity_bundle_R1_-50_R2_-50_L_90_rays_5_20260721_195953.png" 
    alt="Cavity Bundle" 
    width="75%" />
</p>

### Cavity Stability Diagram
<p align="center">
  <img
    src="OUTPUTS/PLOTS/stability_diagram_20260721_195953.png" 
    alt="Cavity Stability Diagram" 
    width="75%" />
</p>

### Animations

#### Concave-Concave Cavity Animation
<p align="center">
  <img src="OUTPUTS/ANIMATIONS/symmetric_concave_concave_cavity_R1_-50.0_R2_-50.0_L_80.0_rc_blue_20260721_205857.gif" alt="Concave-Concave Animation" width="80%" />
</p>

#### Concave-Convex Cavity Animation
<p align="center">
  <img src="OUTPUTS/ANIMATIONS/asymmetric_concave_convex_cavity_R1_-100.0_R2_50.0_L_90.0_rc_blue_20260721_195953.gif" alt="Concave-Convex Animation" width="80%" />
</p>

#### Confocal Cavity Animation
<p align="center">
  <img src="OUTPUTS/ANIMATIONS/confocal_cavity_animation_R1_-80_R2_-80_L_80_20260722_025818.gif" alt="Confocal Animation" width="80%" />
</p>

#### Cavity Bundle Animation
<p align="center">
  <img src="OUTPUTS/ANIMATIONS/cavity_bundle_R1_-50_R2_-50_L_90_rays_5_20260721_195953.gif" alt="Bundle Animation" width="80%" />
</p>

---

## 📂 Project Structure

```text
├── app.py                     # Streamlit application entry point & UI flow
├── cavity_ray_tracing.py      # Core physics engine (ABCD matrix calculations)
├── plotting.py                # Plotly integration for static & animated figures
├── presets.py                 # Cavity configurations and constants
├── export_utils.py            # PNG and GIF/MP4 export handlers
├── requirements.txt           # Python dependencies
├── themes/                    # Custom Streamlit UI JSON themes
└── OUTPUTS/                   # Directory containing exported artifacts
    ├── ANIMATIONS/            # Generated GIFs and MP4s
    └── PLOTS/                 # Generated PNG figures
```

---

## 🚀 Getting Started

### Prerequisites

Make sure you have Python 3.9+ installed.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/optical-cavity-ray-tracing.git
   cd optical-cavity-ray-tracing
   ```

2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure you have `ffmpeg` installed on your system if you plan to export animations as MP4.*

### Running the App

Launch the application using Streamlit:

```bash
streamlit run app.py
```

The app will open automatically in your default web browser at `http://localhost:8501`.

---

## 🛠️ Usage Notes

1. **Configure the Cavity:** Open the sidebar and choose an initial configuration from the dropdown, or manually tune the Radius of Curvature ($R_1, R_2$) and Cavity Length ($L$).
2. **Ray Parameters:** Adjust the initial ray height ($y_0$) and angle ($\theta_0$), or enable a "Ray Bundle" to visualize multiple paths at once.
3. **Visuals:** Customize colors and theming.
4. **Export:** Scroll to the bottom of the page to export the current static view as a high-resolution PNG or render the ray trace as an animation.

---

## 📜 License

This project is licensed under the MIT License.
