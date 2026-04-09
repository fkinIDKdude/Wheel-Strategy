// =============================================================================
// POCKET STYLIST — STATIC RULES DATABASE
// This is the immutable source-of-truth for all styling logic.
// The engine reads from this database; it never mutates it.
// =============================================================================

import {
  Archetype,
  VerticalRatio,
  HorizontalRatio,
  ValueContrast,
  ShoulderSlope,
  NeckLength,
  JawShape,
} from "./models";

// ---------------------------------------------------------------------------
// RULE FRAGMENT TYPES
// ---------------------------------------------------------------------------

export interface FabricRule {
  approved: string[];
  avoid: string[];
}

export interface SilhouetteRule {
  approved: string[];
  avoid: string[];
}

export interface ProportionRule {
  trouserRise: string;
  jacketLength: string;
  trouserBreak: string;
  hemlineGuidance: string;
}

export interface ContrastRule {
  strategy: string;
  approvedPalettes: string[];
  avoid: string[];
}

export interface CollarRule {
  approved: string[];
  avoid: string[];
}

// ---------------------------------------------------------------------------
// ARCHETYPE RULES
// ---------------------------------------------------------------------------

export const ARCHETYPE_RULES: Record<
  Archetype,
  { fabric: FabricRule; silhouette: SilhouetteRule; notes: string[] }
> = {
  [Archetype.DRAMATIC]: {
    fabric: {
      approved: [
        "heavyweight wool (14–18oz)",
        "structured canvas-fused tweed",
        "rigid denim (14oz+)",
        "gabardine",
        "duchesse satin (formal)",
        "heavy crepe",
        "leather",
        "structured ponte",
      ],
      avoid: [
        "jersey knits",
        "lightweight linen",
        "soft draping fabrics",
        "open weaves",
        "cashmere (unstructured)",
        "thin cottons",
      ],
    },
    silhouette: {
      approved: [
        "sharp single-breasted tailoring with strong shoulder",
        "long unbroken vertical lines",
        "full-length overcoats",
        "clean, elongated trousers with a sharp crease",
        "structured blazer with no patch pockets",
        "sleek, minimal detailing",
      ],
      avoid: [
        "relaxed or oversized silhouettes",
        "patch pockets and casual detailing",
        "unstructured blazers",
        "gathered or pleated excess",
        "cropped jackets that break the vertical line",
        "busy surface patterns (plaids, heavy checks)",
      ],
    },
    notes: [
      "Long, unbroken vertical lines are the primary design principle.",
      "Hardware, closures, and buttons must be minimal and understated.",
      "One-color or tonal dressing maximizes the vertical line effect.",
    ],
  },

  [Archetype.NATURAL]: {
    fabric: {
      approved: [
        "textured linen",
        "slubbed cotton",
        "matte wool flannel",
        "raw denim",
        "herringbone tweed",
        "brushed cotton",
        "canvas",
        "unconstructed washed wool",
        "jersey (heavyweight)",
      ],
      avoid: [
        "highly polished fabrics (patent, satin)",
        "stiff fused linings",
        "synthetics with sheen",
        "ultra-smooth gabardine",
        "anything that fights the natural body movement",
      ],
    },
    silhouette: {
      approved: [
        "unconstructed or half-canvassed jackets",
        "relaxed, easy shoulder (natural shoulder)",
        "pleated trousers with a fuller thigh",
        "overshirts and workwear-inspired pieces",
        "chore coats and field jackets",
        "roomier, non-tapered fits through the body",
      ],
      avoid: [
        "severely structured shoulder with roping",
        "skintight fits",
        "ultra-formal or stiff construction",
        "fussy detailing or contrived tailoring",
      ],
    },
    notes: [
      "Layering textured pieces reads as sophisticated, not sloppy.",
      "The silhouette must breathe; restrict fitted construction.",
      "Natural shoulder line is non-negotiable — avoid structured roping.",
    ],
  },

  [Archetype.ROMANTIC]: {
    fabric: {
      approved: [
        "wool challis",
        "fine merino (soft drape)",
        "silk blend",
        "modal",
        "soft double-faced jersey",
        "fine cashmere",
        "viscose crepe",
        "supple suede",
      ],
      avoid: [
        "stiff canvas",
        "rigid denim",
        "heavyweight structured wool",
        "coarse tweeds",
        "anything that fights body curves",
      ],
    },
    silhouette: {
      approved: [
        "tapered and fitted through the waist",
        "softly draped shirts",
        "relaxed taper trouser",
        "single-breasted suits with gentle suppression",
        "soft-shoulder construction",
        "curved and rounded design lines",
      ],
      avoid: [
        "boxy, oversized cuts",
        "sharp angular shoulders",
        "straight-leg or baggy trousers",
        "rigid, boxy blazers with no waist suppression",
      ],
    },
    notes: [
      "Waist suppression is essential — the silhouette must acknowledge the waist.",
      "Rounded lapels complement the archetype better than sharp peak lapels.",
      "Avoid sharp geometry; all lines should curve gently.",
    ],
  },

  [Archetype.GAMINE]: {
    fabric: {
      approved: [
        "crisp cotton poplin",
        "tight-woven wool twill",
        "stiff selvedge denim",
        "compact knit (fine gauge)",
        "crisp broadcloth",
        "polished cotton",
        "light structured wool",
      ],
      avoid: [
        "heavy, voluminous fabrics",
        "chunky knits",
        "heavyweight overwear that overwhelms the frame",
        "flowing, unconstructed drapes",
      ],
    },
    silhouette: {
      approved: [
        "cropped jackets that end at or above the hip",
        "short-rise, slim trousers",
        "two-piece sets with deliberate breaks (jacket hem, trouser waistband)",
        "visual contrast between top and bottom half",
        "close-fitting, compact silhouettes",
        "deliberate line breaks via tuck or waistband",
      ],
      avoid: [
        "long, unbroken vertical lines",
        "oversized or long coats",
        "full-length pieces with no interruption",
        "relaxed, shapeless fits",
      ],
    },
    notes: [
      "Visual interruption of the vertical line is the primary design tool.",
      "Contrast between the top and bottom half is desirable, not a mistake.",
      "Scale of print and detail must remain small to suit the compact frame.",
    ],
  },

  [Archetype.CLASSIC]: {
    fabric: {
      approved: [
        "mid-weight worsted wool (10–12oz)",
        "smooth cotton twill",
        "fine flannel",
        "piqué",
        "medium-weight linen",
        "smooth merino",
        "plain-weave poplin",
      ],
      avoid: [
        "extreme textures (very coarse or very shiny)",
        "fabrics with strong character (slub, raw, distressed)",
        "anything that creates visual noise or asymmetry",
      ],
    },
    silhouette: {
      approved: [
        "perfectly symmetrical tailoring",
        "notch lapel single-breasted suit",
        "medium-taper trouser",
        "balanced proportions (no extremes in any direction)",
        "classic polo and chino combinations",
        "structured but not stiff construction",
      ],
      avoid: [
        "extreme silhouettes in any direction (very oversized, very tight)",
        "asymmetric design details",
        "very bold pattern mixing",
        "strong stylistic statements that read as trendy",
      ],
    },
    notes: [
      "The Classic excels at 'correct' — avoid anything that reads as a strong statement.",
      "Medium is the operating principle: medium weight, medium taper, medium contrast.",
      "Quality of construction matters more than stylistic boldness.",
    ],
  },
};

// ---------------------------------------------------------------------------
// VERTICAL RATIO (PROPORTION) RULES
// ---------------------------------------------------------------------------

export const VERTICAL_RATIO_RULES: Record<VerticalRatio, ProportionRule> = {
  [VerticalRatio.LONG_TORSO_SHORT_LEGS]: {
    trouserRise: "High-rise (natural waist or above). Raises the visual waistline to shorten apparent torso.",
    jacketLength: "Cropped to above the hip. Jacket must end before the crotch point to visually lengthen the leg.",
    trouserBreak: "No break. Full-length clean hem or slight hem tape. A break shortens an already short leg.",
    hemlineGuidance:
      "Trouser hem must land cleanly at the shoe break point — no pooling. Cropped hems (ankle) are permitted if trouser is slim.",
  },
  [VerticalRatio.SHORT_TORSO_LONG_LEGS]: {
    trouserRise: "Mid-to-low rise. Avoid high-rise; it shortens an already short torso and creates a compressed look.",
    jacketLength: "Standard or long hem (below hip). Longer jacket length extends the torso visually.",
    trouserBreak: "A slight break (half-break) is acceptable and softens the long leg line. Full break only with wide, formal trousers.",
    hemlineGuidance:
      "Hemlines must not intersect mid-thigh or mid-calf. Land hems at the knee or at the ankle, never between.",
  },
  [VerticalRatio.BALANCED]: {
    trouserRise: "Mid-rise standard. Maintain proportional balance — do not over-correct in either direction.",
    jacketLength: "Standard hip-length jacket. Slight variation tolerated based on archetype.",
    trouserBreak: "Quarter to half-break. Avoids both extremes.",
    hemlineGuidance:
      "Maintain the 50/50 visual split at the natural waistline. Avoid hemlines that dramatically distort this ratio.",
  },
};

// ---------------------------------------------------------------------------
// HORIZONTAL RATIO (DROP) RULES
// ---------------------------------------------------------------------------

export const HORIZONTAL_RATIO_RULES: Record<
  HorizontalRatio,
  { strategy: string; approved: string[]; avoid: string[] }
> = {
  [HorizontalRatio.V_TAPER]: {
    strategy: "Maintain and celebrate the existing taper. Do not add bulk to the shoulders.",
    approved: [
      "fitted and tapered jackets that follow the V naturally",
      "medium to slim trouser to complement the upper-body V",
      "horizontal trouser details (pleats, cuffs) to add lower weight",
      "open-collar shirts to avoid exaggerating the width",
    ],
    avoid: [
      "strong roped or padded shoulders (exaggerates beyond natural)",
      "very narrow trousers that emphasize the inverted triangle",
      "wide lapels that add apparent shoulder width",
    ],
  },
  [HorizontalRatio.STRAIGHT]: {
    strategy: "Build visual shoulder width to create the appearance of a taper.",
    approved: [
      "structured shoulder with slight roping",
      "horizontal shoulder seams (not raglan)",
      "double-breasted jackets for visual chest width",
      "peak lapels",
      "fitted through the waist to create contrast with shoulder",
      "epaulettes and yoke detailing",
    ],
    avoid: [
      "raglan or drop shoulders that eliminate the shoulder line",
      "boxy fits with no waist shaping",
      "vertical stripes that emphasize the straight line",
    ],
  },
  [HorizontalRatio.MIDSECTION_WEIGHT]: {
    strategy: "Draw the eye upward. Minimize visual attention on the midsection.",
    approved: [
      "structured jackets worn closed",
      "vertical design lines (pinstripes, center seams)",
      "v-necks and open collars to draw the eye upward",
      "darker, solid colors through the midsection",
      "undarted trousers with a clean fall from the waist",
      "medium-to-high rise to smooth the silhouette",
    ],
    avoid: [
      "tucked shirts that emphasize the waistband",
      "horizontal stripes through the midsection",
      "belts with large or decorative buckles at the waist",
      "fitted knits that conform to the midsection",
      "low-rise trousers that create a 'muffin top' line",
    ],
  },
};

// ---------------------------------------------------------------------------
// VALUE CONTRAST RULES
// ---------------------------------------------------------------------------

export const VALUE_CONTRAST_RULES: Record<ValueContrast, ContrastRule> = {
  [ValueContrast.HIGH]: {
    strategy:
      "Stark, high-contrast color blocking. The face demands strong value contrast in the outfit to feel balanced.",
    approvedPalettes: [
      "Navy jacket + white shirt (classic high-contrast block)",
      "Black and ivory",
      "Charcoal and crisp white",
      "Deep burgundy and pale grey",
      "Bold block color: one strong anchor piece (navy, black, forest green)",
    ],
    avoid: [
      "Tonal head-to-toe outfits (they wash out the high-contrast face)",
      "Muddy mid-tone colors with no clear value anchor",
      "Outfits where all pieces are in the medium-value range",
    ],
  },
  [ValueContrast.MEDIUM]: {
    strategy:
      "Moderate contrast. Mix tones that are related but not identical. Avoid extremes in both directions.",
    approvedPalettes: [
      "Stone trousers + mid-blue shirt",
      "Camel and brown",
      "Navy and grey",
      "Soft earth tones with one slightly contrasting accent",
    ],
    avoid: [
      "Pure black with pure white (too stark)",
      "Full monochromatic with no differentiation",
    ],
  },
  [ValueContrast.LOW]: {
    strategy:
      "Tonal, monochromatic dressing. Outfit value should match the face's lack of contrast — avoid stark blocking.",
    approvedPalettes: [
      "All-navy (different textures, same value family)",
      "Tonal grey (light grey shirt, mid-grey trouser, charcoal jacket)",
      "Earth tone monochrome (sand, camel, tan)",
      "Soft-on-soft: cream shirt, oatmeal trouser, light tan jacket",
      "Different textures within the same color family",
    ],
    avoid: [
      "High-contrast color blocking (navy + white, black + cream)",
      "Bold graphic patterns with strong value contrast",
      "Any outfit where the 'light' and 'dark' pieces are extreme opposites",
    ],
  },
};

// ---------------------------------------------------------------------------
// POSTURE & GEOMETRY RULES
// ---------------------------------------------------------------------------

export const SHOULDER_SLOPE_RULES: Record<
  ShoulderSlope,
  { approved: string[]; avoid: string[] }
> = {
  [ShoulderSlope.ROUNDED]: {
    approved: [
      "structured jackets with built shoulder (minimal padding, just structure)",
      "canvas-fused or structured shoulder seams",
      "yoke construction across the back shoulder",
      "shirts with a clean, set-in sleeve at the natural shoulder point",
    ],
    avoid: [
      "raglan sleeves (eliminate the shoulder line entirely)",
      "soft, unconstructed shoulders that follow the slope",
      "drop-shoulder construction",
      "overly heavy shoulder padding that looks theatrical",
    ],
  },
  [ShoulderSlope.SQUARE]: {
    approved: [
      "natural shoulder construction (no padding needed)",
      "soft, unconstructed jackets that don't over-structure",
      "raglan or slightly dropped shoulder tolerated for casual wear",
    ],
    avoid: [
      "strong roped shoulder or heavy padding (creates an 'armored' look)",
    ],
  },
};

export const NECK_LENGTH_RULES: Record<
  NeckLength,
  { approved: string[]; avoid: string[]; collarTypes: CollarRule }
> = {
  [NeckLength.SHORT_THICK]: {
    approved: [
      "V-neck shirts and sweaters (deepens the apparent neck length)",
      "unbuttoned point collars (2 buttons open minimum)",
      "open spread collars worn open",
      "scoop necks for knitwear",
      "lower necklines in general",
    ],
    avoid: [
      "high crew necks (strictly forbidden — visually eliminates the neck)",
      "turtlenecks and mock necks",
      "button-to-the-top point collars",
      "round-neck sweaters worn without a V-neck undershirt",
      "thick scarves or neckerchiefs worn high",
      "very wide, high-set collars",
    ],
    collarTypes: {
      approved: ["point collar (worn open)", "spread collar (worn open)", "V-neck", "open-throat button-down"],
      avoid: ["band collar (worn closed)", "Mandarin collar", "funnel neck", "turtleneck", "crew neck"],
    },
  },
  [NeckLength.LONG_THIN]: {
    approved: [
      "turtlenecks and mock necks (fill and balance the neck)",
      "crew necks",
      "high-button point collars",
      "layered scarves and neckerchiefs",
      "boat necks",
    ],
    avoid: [
      "very deep V-necks that further elongate",
      "open-throat collar with no layer below",
    ],
    collarTypes: {
      approved: ["turtleneck", "mock neck", "crew neck", "band collar", "Mandarin collar", "high-button point"],
      avoid: ["deep V-neck", "very low scoop"],
    },
  },
  [NeckLength.AVERAGE]: {
    approved: ["all standard collar types tolerated"],
    avoid: ["no absolute avoidances — use archetype and contrast to guide preference"],
    collarTypes: {
      approved: ["all standard collar types"],
      avoid: [],
    },
  },
};

export const JAW_SHAPE_RULES: Record<
  JawShape,
  { approved: string[]; avoid: string[]; collarTypes: CollarRule }
> = {
  [JawShape.WIDE_SQUARE]: {
    approved: [
      "spread collars (the wide angle echoes and frames the jaw symmetrically)",
      "open-collar looks",
      "soft, curved lapel shapes",
      "medium-width lapels",
    ],
    avoid: [
      "very narrow point collars (creates visual contrast that emphasizes jaw width)",
      "very high, closed collars that frame the jaw tightly",
    ],
    collarTypes: {
      approved: ["spread collar", "semi-spread collar", "open collar", "wide-spread"],
      avoid: ["very narrow point collar", "pinhole collar", "tab collar"],
    },
  },
  [JawShape.NARROW]: {
    approved: [
      "point collars (the narrow angle echoes the jawline)",
      "button-down collars",
      "medium spread",
    ],
    avoid: [
      "very wide spread collars (makes the jaw appear narrower by contrast)",
    ],
    collarTypes: {
      approved: ["point collar", "button-down collar", "medium spread"],
      avoid: ["very wide spread", "cutaway collar"],
    },
  },
  [JawShape.AVERAGE]: {
    approved: ["most collar types tolerated"],
    avoid: [],
    collarTypes: {
      approved: ["all standard collar types"],
      avoid: [],
    },
  },
};
