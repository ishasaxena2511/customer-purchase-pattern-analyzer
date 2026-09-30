# 🎨 AI Image Generator Prompts: Executive Dashboard GitHub Banner

> [!NOTE]
> **Illustrative Purpose Only**: The prompts in this document are designed to generate high-fidelity conceptual mockups, marketing hero banners, or social media cover art. In technical repositories, recruiter portfolios, and the primary [`README.md`](../README.md), **real automated screenshots** from the running Streamlit application (located in [`images/`](../images/)) should always be used to demonstrate genuine working software and data integrity.

---

## 📐 Design & Layout Specification Matrix

To produce an authentic, pixel-accurate representation of the **Customer Purchase Pattern Analyzer**, the prompt incorporates the exact design tokens, components, and layout architecture of the production Streamlit application:

| Element | Specification in Application | Visual Details in Prompt |
| :--- | :--- | :--- |
| **Color Palette** | Navy `#0B2545`, Teal `#13A89E`, Amber `#F59E0B`, Emerald `#10B981`, Slate `#F8FAFC` | Corporate deep navy header, vibrant teal line chart accents, crisp white cards |
| **Header Banner** | Linear gradient (`#0B2545` to `#134074`) with title & subtitle | Sleek dark navy enterprise SaaS banner with white typography |
| **Sidebar** | 300px fixed width, light gray canvas `#F8FAFC` | Filter panel with date range and teal multi-select tag badges (`North`, `Electronics`, etc.) |
| **KPI Section** | 5 uniform white cards with top borders and soft drop shadows | Cards displaying **₹3.77M Revenue**, **129 Customers**, **₹3.3K AOV**, **88.4% Repeat**, **₹87.7K CLV** |
| **Middle Charts** | 3-column container grid | Teal Revenue Trajectory line, Horizontal Segment Bar, Vertical Category Sales Bar |
| **Typography** | Segoe UI / Inter, bold headings, muted slate subtext `#64748B` | Clean modern sans-serif typography, high legibility, crisp numbers |

---

## 🌟 1. Detailed Master Prompt (Full Specification)

*Recommended for: **Midjourney v6**, **DALL-E 3**, **Stable Diffusion XL (SDXL)**, **Google Imagen 3***

```text
An ultra-high-resolution, professional executive SaaS dashboard interface for a retail analytics web application called "Customer Purchase Pattern Analyzer", modern corporate desktop UI design. 

The color theme uses an elegant corporate palette of Deep Navy (#0B2545), Dynamic Vibrant Teal (#13A89E), Soft Emerald Green (#10B981), Amber Gold (#F59E0B), and Crisp White cards on an ultra-light slate gray canvas (#F8FAFC).

Layout structure:
- Left sidebar: Dark slate-tinted filter panel titled "Executive Filters" featuring interactive dropdowns, calendar date range picker, and vibrant teal tag pills for "North", "Clothing", "Electronics", and "UPI".
- Top executive banner: Deep navy gradient banner (#0B2545 to #134074) with a modern retail analytics icon and clean white title "Executive Purchase Pattern & Revenue Analyzer" with subtext "Enterprise Retail Analytics • Dynamic Cohorts • Churn Risk & Strategic Recommendations".
- Top row of 5 white KPI metric cards with subtle borders and soft shadows:
  1. "TOTAL REVENUE: ₹3.77M" with green badge "▲ +75.7% vs prior half"
  2. "TOTAL CUSTOMERS: 129" with green badge "▲ +9.3% vs prior half"
  3. "AVG ORDER VALUE (AOV): ₹3.3K" with red badge "▼ -9.9% vs prior half"
  4. "REPEAT PURCHASE RATE: 88.4%" with green badge "▲ +4.5 pts"
  5. "CUSTOMER LIFETIME VALUE: ₹87.7K" with red badge "▼ -6.2%"
- Middle section with 3 white rectangular card containers:
  1. Left card: "Revenue Trajectory" with a smooth, glowing teal line chart, light teal shaded area underneath, and a minimalist toggle switch labeled "MoM %".
  2. Center card: "Segment Revenue" showing a clean horizontal bar chart with dark navy for "Champions (56.2%)" and vibrant teal for "Loyal Customers (21.3%)".
  3. Right card: "Category Sales" showing sharp vertical dark navy bar charts for Electronics, Sports, and Clothing, with an interactive "Margin %" toggle.

Figma UI presentation, Dribbble trending, Behance award-winning dashboard, pixel-perfect alignment, razor-sharp vector charts, elegant drop shadows, clean modern typography in Inter and Segoe UI, photorealistic software screenshot, 8k resolution, flat clean UI view without laptop frame or angled perspective. --ar 16:9 --style raw --v 6.0
```

---

## ⚡ 2. Shorter Version (For Character-Limited Prompts)

*Recommended for: **Midjourney Quick / Fast Mode**, **Bing Image Creator**, **Canva Magic Media***

```text
UI mockup of a modern enterprise retail analytics dashboard named "Customer Purchase Pattern Analyzer". Corporate color palette of Deep Navy (#0B2545), Dynamic Teal (#13A89E), and White cards on light gray background. Left sidebar with filter tags. Top dark navy gradient banner. Top row of 5 clean KPI cards showing Total Revenue (₹3.77M), Customers (129), AOV (₹3.3K), Repeat Rate (88.4%), and CLV (₹87.7K) with colored delta indicators. Middle section with 3 cards: a smooth teal monthly revenue trajectory line chart, a horizontal customer segment bar chart, and vertical category sales bars. Minimalist modern SaaS interface, Figma UI design, clean typography, 8k, flat front-facing desktop view. --ar 16:9
```

---

## 🚫 3. Negative Prompt

*Use this in **Stable Diffusion**, **Midjourney (`--no`)**, or engines supporting negative guidance to eliminate common AI UI artifacts:*

```text
--no laptop frame, computer monitor bezel, slanted angle, 3d isometric tilt, distorted text, gibberish numbers, blurry charts, cartoon illustration, childish 3d render, oversaturated rainbow colors, neon pink, messy layout, overlapping elements, cut-off cards, clipped borders, watermark, stock photo watermark, low resolution, grain, JPEG artifacts, dark mode, amateur design
```

*(For Stable Diffusion Negative Prompt text box:)*
```text
laptop frame, monitor bezel, slanted angle, 3D isometric tilt, skewed perspective, distorted text, unreadable characters, blurry charts, cartoon, childish illustration, 3D glossy icons, oversaturated rainbow colors, neon magenta, messy layout, overlapping boxes, cut-off text, clipped cards, low quality, pixelated, JPEG artifacts, watermark, logo overlay, dark theme, amateur UI
```

---

## 🛠️ 4. Recommended Midjourney & Tool Parameters

| Parameter Flag | Purpose | Recommended Value |
| :--- | :--- | :--- |
| `--ar 16:9` | Standard widescreen hero banner for GitHub and LinkedIn | `16:9` (or `21:9` for ultra-wide header) |
| `--v 6.0` | Latest Midjourney model with photorealistic font rendering | `6.0` |
| `--style raw` | Prevents overly stylized/artistic flourishes; preserves flat UI realism | Enabled |
| `--stylize` | Controls creativity vs prompt fidelity | `150` to `250` (lower is more accurate to UI) |

---

## 💡 5. Pro Tips for GitHub Repository Showcase

1. **GitHub Banner Sizing**: GitHub README headers look optimal at **1280 × 640 px** or **1920 × 1080 px** (16:9 ratio).
2. **Overlaying Logo & Badges**: If you generate an image using this prompt, you can easily open it in Figma or Canva to overlay your GitHub repository title, your name, and tech stack badges (Python, Streamlit, SQLite, Scikit-Learn) on top of the image canvas.
3. **Keep Real Proof in the README**: Keep the generated banner as the top decorative header of your repository, while retaining the real screenshots (`images/dashboard_full.png`, `images/kpi_section.png`, etc.) in the **"Executive BI Dashboard"** section of your [`README.md`](../README.md) to provide authentic technical proof to recruiters and hiring managers.
