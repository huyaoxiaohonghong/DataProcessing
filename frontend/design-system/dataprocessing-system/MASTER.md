# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** DataProcessing System
**Generated:** 2026-03-30
**Style:** Glassmorphism + Dark Mode (OLED) + 3D & Hyperrealism
**Stack:** Vue 3 + Ant Design Vue + CSS Custom Properties

---

## Global Rules

### Color Palette (Dark OLED)

| Role | Value | CSS Variable |
|------|-------|--------------|
| Background (OLED) | `#000000` | `--color-bg-base` |
| Background Elevated | `#0A0A0F` | `--color-bg-elevated` |
| Surface / Card | `rgba(255, 255, 255, 0.06)` | `--color-surface` |
| Surface Hover | `rgba(255, 255, 255, 0.10)` | `--color-surface-hover` |
| Primary | `#6366F1` (Indigo) | `--color-primary` |
| Primary Glow | `rgba(99, 102, 241, 0.4)` | `--color-primary-glow` |
| Secondary | `#8B5CF6` (Violet) | `--color-secondary` |
| Accent / CTA | `#F59E0B` (Amber) | `--color-accent` |
| Success | `#10B981` | `--color-success` |
| Danger | `#EF4444` | `--color-danger` |
| Warning | `#F59E0B` | `--color-warning` |
| Text Primary | `#F1F5F9` | `--color-text` |
| Text Secondary | `#94A3B8` | `--color-text-muted` |
| Text Tertiary | `#475569` | `--color-text-dim` |
| Border Glass | `rgba(255, 255, 255, 0.08)` | `--color-border` |
| Border Hover | `rgba(255, 255, 255, 0.15)` | `--color-border-hover` |

### Typography

- **Heading Font:** Fira Code (monospace, technical feel)
- **Body Font:** Fira Sans (clean readability)
- **Mood:** Dashboard, data, analytics, technical, precise

**CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');
```

| Element | Font | Size | Weight | Letter Spacing |
|---------|------|------|--------|----------------|
| H1 | Fira Code | 32px / 2rem | 700 | -0.02em |
| H2 | Fira Code | 24px / 1.5rem | 600 | -0.01em |
| H3 | Fira Code | 18px / 1.125rem | 600 | 0 |
| Body | Fira Sans | 14px / 0.875rem | 400 | 0.01em |
| Caption | Fira Sans | 12px / 0.75rem | 400 | 0.02em |
| Data/Numbers | Fira Code | 14px | 500 | 0.05em |


### Glassmorphism Specs

| Token | Value | Usage |
|-------|-------|-------|
| `--glass-blur` | `backdrop-filter: blur(16px)` | All glass surfaces |
| `--glass-bg` | `rgba(255, 255, 255, 0.06)` | Card / panel background |
| `--glass-bg-hover` | `rgba(255, 255, 255, 0.10)` | Hover state |
| `--glass-border` | `1px solid rgba(255, 255, 255, 0.08)` | Subtle edge |
| `--glass-border-hover` | `1px solid rgba(255, 255, 255, 0.15)` | Hover edge |
| `--glass-shadow` | `0 8px 32px rgba(0, 0, 0, 0.4)` | Depth shadow |

**Implementation:**
```css
.glass-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  transition: all 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
  background: rgba(255, 255, 255, 0.10);
  border-color: rgba(255, 255, 255, 0.15);
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15), 0 16px 48px rgba(0, 0, 0, 0.5);
  transform: translateY(-2px);
}
```

### 3D & Hyperrealism Effects

| Effect | Value | Usage |
|--------|-------|-------|
| Perspective | `perspective: 1000px` | Parent container for 3D children |
| Card Tilt | `transform: rotateX(2deg) rotateY(-2deg)` | Subtle 3D on hover |
| Depth Layers | 3-5 parallax layers | Background depth |
| Glow | `box-shadow: 0 0 20px var(--color-primary-glow)` | Active / focus states |
| Text Glow | `text-shadow: 0 0 10px rgba(99,102,241,0.5)` | Headings, emphasis |
| Animation Duration | `300-400ms` | All 3D transitions |
| Easing | `cubic-bezier(0.4, 0, 0.2, 1)` | Smooth physics feel |

**3D Card Example:**
```css
.card-3d {
  transform-style: preserve-3d;
  transition: transform 400ms cubic-bezier(0.4, 0, 0.2, 1);
}

.card-3d:hover {
  transform: perspective(1000px) rotateX(2deg) rotateY(-3deg) translateZ(10px);
}

.card-3d::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 50%);
  pointer-events: none;
}
```

### Spacing

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` | Tight gaps |
| `--space-sm` | `8px` | Icon gaps |
| `--space-md` | `16px` | Standard padding |
| `--space-lg` | `24px` | Section padding |
| `--space-xl` | `32px` | Large gaps |
| `--space-2xl` | `48px` | Section margins |
| `--space-3xl` | `64px` | Hero padding |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | `8px` | Buttons, inputs |
| `--radius-md` | `12px` | Small cards |
| `--radius-lg` | `16px` | Cards, panels |
| `--radius-xl` | `24px` | Modals, large containers |

---

## Component Specs (Ant Design Vue Overrides)

### Ant Design Theme Token Overrides

```typescript
// Ant Design Vue ConfigProvider theme
const darkGlassTheme = {
  token: {
    colorPrimary: '#6366F1',
    colorBgBase: '#000000',
    colorBgContainer: 'rgba(255, 255, 255, 0.06)',
    colorBgElevated: '#0A0A0F',
    colorBgLayout: '#000000',
    colorBorder: 'rgba(255, 255, 255, 0.08)',
    colorBorderSecondary: 'rgba(255, 255, 255, 0.05)',
    colorText: '#F1F5F9',
    colorTextSecondary: '#94A3B8',
    colorTextTertiary: '#475569',
    borderRadius: 12,
    fontFamily: "'Fira Sans', -apple-system, sans-serif",
    fontFamilyCode: "'Fira Code', monospace",
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
  },
  algorithm: theme.darkAlgorithm,
}
```

### Sider (Sidebar)

```css
.ant-layout-sider {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}
```

### Header

```css
.ant-layout-header {
  background: rgba(255, 255, 255, 0.04) !important;
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
```

### Cards

```css
.ant-card {
  background: rgba(255, 255, 255, 0.06) !important;
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 16px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}
```

### Tables

```css
.ant-table {
  background: transparent !important;
}

.ant-table-thead > tr > th {
  background: rgba(255, 255, 255, 0.04) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #94A3B8 !important;
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.ant-table-tbody > tr > td {
  border-bottom: 1px solid rgba(255, 255, 255, 0.04) !important;
}

.ant-table-tbody > tr:hover > td {
  background: rgba(255, 255, 255, 0.06) !important;
}
```

### Buttons

```css
.ant-btn-primary {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
  transition: all 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

.ant-btn-primary:hover {
  box-shadow: 0 6px 24px rgba(99, 102, 241, 0.5);
  transform: translateY(-1px);
}
```

### Inputs

```css
.ant-input, .ant-select-selector {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 8px !important;
  color: #F1F5F9 !important;
}

.ant-input:focus, .ant-input-focused {
  border-color: #6366F1 !important;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
}
```

### Modals

```css
.ant-modal-content {
  background: rgba(10, 10, 15, 0.95) !important;
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px !important;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6);
}
```

---

## Stat Cards (Dashboard)

```css
.stat-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 24px;
  transform-style: preserve-3d;
  transition: all 400ms cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover {
  transform: perspective(1000px) rotateX(2deg) rotateY(-2deg) translateZ(8px);
  border-color: rgba(255, 255, 255, 0.15);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 0 20px var(--card-glow-color, rgba(99, 102, 241, 0.15));
}

/* Glow accent per card */
.stat-card--primary  { --card-glow-color: rgba(99, 102, 241, 0.2); }
.stat-card--success  { --card-glow-color: rgba(16, 185, 129, 0.2); }
.stat-card--warning  { --card-glow-color: rgba(245, 158, 11, 0.2); }
.stat-card--danger   { --card-glow-color: rgba(239, 68, 68, 0.2); }

.stat-value {
  font-family: 'Fira Code', monospace;
  font-size: 32px;
  font-weight: 700;
  color: #F1F5F9;
  text-shadow: 0 0 10px var(--card-glow-color, rgba(99, 102, 241, 0.3));
}

.stat-label {
  font-family: 'Fira Sans', sans-serif;
  font-size: 13px;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

---

## Background Effects

```css
/* OLED base with subtle gradient orbs */
body {
  background: #000000;
  color: #F1F5F9;
  font-family: 'Fira Sans', -apple-system, sans-serif;
}

/* Ambient glow orbs (behind content) */
.bg-ambient::before,
.bg-ambient::after {
  content: '';
  position: fixed;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.15;
  pointer-events: none;
  z-index: 0;
}

.bg-ambient::before {
  width: 600px; height: 600px;
  top: -200px; right: -100px;
  background: radial-gradient(circle, #6366F1, transparent 70%);
}

.bg-ambient::after {
  width: 500px; height: 500px;
  bottom: -150px; left: -100px;
  background: radial-gradient(circle, #8B5CF6, transparent 70%);
}
```

---

## Anti-Patterns (Do NOT Use)

- ❌ Light backgrounds (`#FFFFFF`, `#F8FAFC`) — OLED means pure black `#000`
- ❌ Opaque card backgrounds — Always use translucent glass
- ❌ Emojis as icons — Use SVG (Ant Design Icons)
- ❌ Missing `cursor: pointer` on clickable elements
- ❌ Layout-shifting hover (scale transforms that push siblings)
- ❌ Instant state changes — Always 200-400ms transitions
- ❌ Heavy 3D on every element — Reserve for key interactive cards only
- ❌ White text on glass without sufficient contrast
- ❌ Slow rendering — Limit backdrop-filter to visible cards only

---

## Pre-Delivery Checklist

- [ ] Pure black `#000` background (OLED)
- [ ] All cards use glass effect (blur + translucent bg + border)
- [ ] 3D hover effects on stat cards and key interactive elements
- [ ] Glow accents on primary actions and active states
- [ ] Fira Code for headings/data, Fira Sans for body
- [ ] `cursor: pointer` on all clickable elements
- [ ] Transitions 200-400ms with cubic-bezier easing
- [ ] Text contrast ≥ 4.5:1 on glass surfaces
- [ ] `prefers-reduced-motion` disables 3D transforms and glow animations
- [ ] Responsive: 375px, 768px, 1024px, 1440px
- [ ] No content hidden behind fixed navbars
