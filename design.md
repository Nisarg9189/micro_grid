You are an expert frontend engineer, UI/UX designer, and visual design specialist.

I want you to redesign my existing frontend using the following design direction.

## MAIN OBJECTIVE

Transform the current UI into a **premium LIGHT / WHITE Bitcoin DeFi interface**.

IMPORTANT:

* The current design may contain black/dark backgrounds.
* Replace the dark/black visual foundation with a clean WHITE / LIGHT foundation.
* Do NOT simply invert colors.
* Preserve the Bitcoin DeFi identity, technical feel, premium appearance, animations, gradients, and visual hierarchy.
* The final result must look intentionally designed, not like a generic SaaS dashboard or default Tailwind theme.

## COLOR SYSTEM

Use these colors consistently:

* Background: `#FFFFFF`
* Secondary Background: `#F8FAFC`
* Card Surface: `#FFFFFF`
* Elevated Surface: `#FFFFFF`
* Primary Text: `#0F172A`
* Secondary Text: `#64748B`
* Border: `#E2E8F0`
* Bitcoin Orange: `#F7931A`
* Burnt Orange: `#EA580C`
* Digital Gold: `#FFD600`

Primary gradient:

`linear-gradient(to right, #EA580C, #F7931A)`

Premium gradient:

`linear-gradient(to right, #F7931A, #FFD600)`

## VISUAL STYLE

The interface should feel:

* Premium
* Financial
* Technical
* Trustworthy
* Modern
* Clean
* High-end
* Data-driven
* Bitcoin / DeFi inspired

Think:

**Bitcoin infrastructure + modern financial terminal + premium light interface.**

Avoid:

* Generic corporate SaaS design
* Excessive rounded cards
* Flat boring white pages
* Excessive shadows
* Random colors
* Purple/blue SaaS gradients
* Dark-mode remnants
* Heavy black shadows

## BACKGROUND

Use a bright white background.

Create subtle visual depth using:

* Very light grid patterns
* Orange radial gradients
* Gold radial gradients
* Soft blur effects
* Very subtle noise/textures

Example grid:

```css
background-size: 50px 50px;

background-image:
  linear-gradient(to right, rgba(148, 163, 184, 0.15) 1px, transparent 1px),
  linear-gradient(to bottom, rgba(148, 163, 184, 0.15) 1px, transparent 1px);
```

The grid must be subtle and never interfere with readability.

## CARDS

Use:

```text
bg-white
border border-slate-200
rounded-2xl
```

Cards should have generous spacing.

Normal:

```text
shadow-[0_10px_40px_rgba(15,23,42,0.05)]
```

Hover:

```text
-translate-y-1
border-[#F7931A]/50
shadow-[0_0_30px_-10px_rgba(247,147,26,0.2)]
```

Use subtle orange/gold glow instead of heavy black shadows.

## GLASSMORPHISM

For floating components use:

```text
bg-white/70
backdrop-blur-lg
border border-white/80
```

Add very subtle elevation.

Do not make glass components dark.

## BUTTONS

### Primary Button

Use:

```text
bg-gradient-to-r from-[#EA580C] to-[#F7931A]
text-white
rounded-full
font-semibold
uppercase
tracking-wider
```

Add subtle orange glow.

Hover:

```text
scale-105
```

### Secondary Button

Use:

```text
bg-white
border-2 border-slate-300
text-slate-900
rounded-full
```

Hover:

```text
border-[#F7931A]
bg-orange-50
```

### Ghost Button

Use:

```text
text-slate-700
```

Hover:

```text
bg-orange-50
text-[#F7931A]
```

## TYPOGRAPHY

Use:

### Headings

`Space Grotesk`

Use for:

* Hero headings
* Section headings
* Card titles
* Navigation headings

### Body

`Inter`

Use for:

* Paragraphs
* Descriptions
* Buttons
* General UI

### Technical/Data

`JetBrains Mono`

Use for:

* Prices
* Statistics
* Numbers
* Badges
* Technical information
* Blockchain/network information

Hero heading:

```text
text-4xl sm:text-5xl md:text-7xl
font-heading
font-bold
leading-tight
```

## GRADIENT HEADLINES

Use Bitcoin gradients selectively.

For important words in hero headings:

```text
bg-gradient-to-r from-[#F7931A] to-[#FFD600]
bg-clip-text
text-transparent
```

Do not make the entire page gradient-heavy.

## ICONS

Use `lucide-react`.

Colors:

```text
text-[#F7931A]
text-[#EA580C]
text-[#FFD600]
text-slate-500
text-slate-900
```

Icon containers:

```text
bg-orange-50
border border-orange-200
rounded-lg
p-3
```

Add subtle orange glow on hover.

## HERO SECTION

Create a strong premium hero.

Include:

* Large typography
* Bitcoin orange/gold gradient accent
* Subtle blockchain grid
* Soft orange/gold radial glow
* Floating statistics
* Orbital/ring visual if appropriate
* Technical data elements

Use animation carefully.

The hero should immediately communicate:

**Financial intelligence + Bitcoin + technology + trust.**

## ANIMATIONS

Animations should be smooth and purposeful.

Use:

```text
transition-all duration-300
```

Card hover:

```text
hover:-translate-y-1
```

Button hover:

```text
hover:scale-105
```

Floating elements can use:

```css
@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-20px);
  }
}
```

Use orbital animations where appropriate:

```text
animate-[spin_10s_linear_infinite]
```

Respect:

```css
prefers-reduced-motion
```

and reduce/disable animations when necessary.

## BLOCKCHAIN VISUAL LANGUAGE

Use visual elements inspired by blockchain infrastructure:

* Nodes
* Connected lines
* Grid structures
* Timeline nodes
* Data blocks
* Technical labels
* Hash-like metadata
* Network indicators

Do not overuse crypto clichés.

Keep the design sophisticated.

## "HOW IT WORKS"

Represent the process as a blockchain-style timeline.

Use:

* Orange vertical gradient line
* Circular numbered nodes
* White cards
* Orange corner accents
* Subtle grid background

Example concept:

```text
   ●
   │
   │
 ┌──────────────┐
 │ Step 01      │
 │ Connect      │
 └──────────────┘
   │
   ●
   │
 ┌──────────────┐
 │ Step 02      │
 │ Analyze      │
 └──────────────┘
```

## PRICING

Create intentional visual hierarchy.

Popular plan:

```text
scale-105
border-[#F7931A]
shadow-[0_0_40px_-10px_rgba(247,147,26,0.2)]
```

Other plans should remain visually quieter.

On mobile remove the scale effect.

## INPUTS

Use clean technical inputs:

```text
bg-slate-50
border-b-2 border-slate-200
text-slate-900
placeholder:text-slate-400
```

Focus:

```text
focus-visible:border-[#F7931A]
focus-visible:outline-none
focus-visible:ring-2
focus-visible:ring-[#F7931A]/20
```

## RESPONSIVE DESIGN

Mobile-first.

Breakpoints:

* `sm`: 640px
* `md`: 768px
* `lg`: 1024px
* `xl`: 1280px

Desktop:

* Spacious layouts
* Large hero
* Multi-column sections
* Floating visual elements

Mobile:

* Single-column layouts
* Smaller hero graphics
* Stacked cards
* No excessive horizontal overflow
* Minimum 44px touch targets

## ACCESSIBILITY

Maintain or improve accessibility.

Ensure:

* Strong text contrast
* Visible focus states
* Semantic HTML
* Proper heading hierarchy
* Descriptive image alt text
* Keyboard navigation
* Accessible buttons
* Reduced-motion support

Do not use light gray text that becomes difficult to read on white backgrounds.

## IMPORTANT IMPLEMENTATION RULES

Before changing anything:

1. Inspect the existing project.
2. Identify the framework.
3. Identify Tailwind/shadcn/custom CSS usage.
4. Inspect existing components.
5. Inspect existing color tokens.
6. Understand the current page structure.
7. Reuse existing components where possible.
8. Do not unnecessarily rewrite working functionality.
9. Do not change business logic unless required.
10. Preserve existing API integrations and functionality.

Then implement the redesign.

## CODE QUALITY

Keep the implementation:

* Componentized
* Reusable
* Responsive
* Maintainable
* Consistent
* Type-safe where applicable

Centralize design tokens instead of scattering arbitrary colors throughout the project.

Avoid unnecessary one-off CSS.

## FINAL DESIGN TEST

After implementation, review the UI visually and check:

* Is the background genuinely light/white?
* Are there any unwanted dark-mode remnants?
* Is text readable?
* Are Bitcoin orange/gold accents prominent but not excessive?
* Does the UI feel premium?
* Do cards have appropriate depth?
* Are hover states polished?
* Does mobile look intentional?
* Does the interface look like Bitcoin/DeFi rather than generic SaaS?
* Are animations smooth and purposeful?
* Is accessibility maintained?

If something looks generic, improve the visual design rather than accepting the first implementation.

IMPORTANT FINAL REQUIREMENT:

**Do not merely replace black with white. Redesign the visual relationships for a light interface while preserving the original Bitcoin DeFi personality.**
