// =============================================================================
// POCKET STYLIST — DATA MODELS
// Core type definitions for user physical profile inputs.
// These interfaces represent the extracted measurements from user photos.
// =============================================================================

// ---------------------------------------------------------------------------
// ENUMS — All discrete input categories
// ---------------------------------------------------------------------------

export enum VerticalRatio {
  LONG_TORSO_SHORT_LEGS = "LONG_TORSO_SHORT_LEGS",
  SHORT_TORSO_LONG_LEGS = "SHORT_TORSO_LONG_LEGS",
  BALANCED = "BALANCED",
}

export enum HorizontalRatio {
  V_TAPER = "V_TAPER",            // Shoulder notably wider than waist
  STRAIGHT = "STRAIGHT",          // Shoulder and waist close in width
  MIDSECTION_WEIGHT = "MIDSECTION_WEIGHT", // Waist at/wider than shoulder
}

export enum ValueContrast {
  HIGH = "HIGH",     // Strong luminance delta between hair and skin
  MEDIUM = "MEDIUM", // Moderate luminance delta
  LOW = "LOW",       // Minimal luminance delta (tonal similarity)
}

export enum Archetype {
  DRAMATIC = "DRAMATIC",   // Sharp bone structure, taut/lean flesh
  NATURAL = "NATURAL",     // Blunt bone, broad/muscular flesh
  ROMANTIC = "ROMANTIC",   // Delicate bone, soft/rounded flesh
  GAMINE = "GAMINE",       // Compact/angular bone, taut flesh, small scale
  CLASSIC = "CLASSIC",     // Symmetrical bone, even/moderate flesh
}

export enum ShoulderSlope {
  ROUNDED = "ROUNDED",  // Sloped, soft shoulder line
  SQUARE = "SQUARE",    // Flat, angular shoulder line
}

export enum NeckLength {
  SHORT_THICK = "SHORT_THICK", // Short neck, wide circumference
  LONG_THIN = "LONG_THIN",     // Long neck, narrow circumference
  AVERAGE = "AVERAGE",
}

export enum JawShape {
  WIDE_SQUARE = "WIDE_SQUARE",   // Broad, angular jaw
  NARROW = "NARROW",             // Pointed or narrow jaw
  AVERAGE = "AVERAGE",
}

// ---------------------------------------------------------------------------
// USER PROFILE — The complete physical input object
// ---------------------------------------------------------------------------

export interface UserProfile {
  archetype: Archetype;
  verticalRatio: VerticalRatio;
  horizontalRatio: HorizontalRatio;
  valueContrast: ValueContrast;
  shoulderSlope: ShoulderSlope;
  neckLength: NeckLength;
  jawShape: JawShape;
}
