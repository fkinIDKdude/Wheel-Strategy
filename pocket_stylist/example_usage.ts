// =============================================================================
// POCKET STYLIST — EXAMPLE USAGE
// Demonstrates how to call the engine with two contrasting profiles.
// Paste this into Google AI Studio as context, or run via ts-node.
// =============================================================================

import { generateRecommendations } from "./engine";
import {
  UserProfile,
  Archetype,
  VerticalRatio,
  HorizontalRatio,
  ValueContrast,
  ShoulderSlope,
  NeckLength,
  JawShape,
} from "./models";

// ---------------------------------------------------------------------------
// PROFILE A: Dramatic archetype, long torso, high contrast, short/thick neck
// ---------------------------------------------------------------------------

const profileA: UserProfile = {
  archetype: Archetype.DRAMATIC,
  verticalRatio: VerticalRatio.LONG_TORSO_SHORT_LEGS,
  horizontalRatio: HorizontalRatio.V_TAPER,
  valueContrast: ValueContrast.HIGH,
  shoulderSlope: ShoulderSlope.SQUARE,
  neckLength: NeckLength.SHORT_THICK,
  jawShape: JawShape.WIDE_SQUARE,
};

const recommendationsA = generateRecommendations(profileA);

console.log("=== PROFILE A RECOMMENDATIONS ===");
console.log(JSON.stringify(recommendationsA, null, 2));

/*
Expected output highlights for Profile A:
- Fabrics: heavyweight wool, gabardine, structured canvas — long unbroken lines
- Silhouette: sharp tailoring, no patch pockets, elongated creased trousers
- Trouser rise: HIGH-RISE (long torso demands this to shorten the torso visually)
- Jacket length: CROPPED (end before crotch to lengthen the leg line)
- Trouser break: NO BREAK (short legs cannot afford any break)
- Collar: spread collar (jaw), STRICTLY NO turtlenecks/crew necks (short thick neck)
- Contrast: navy + white, stark color blocking
- Primary principle: unbroken vertical line
*/

// ---------------------------------------------------------------------------
// PROFILE B: Natural archetype, short torso, low contrast, rounded shoulders
// ---------------------------------------------------------------------------

const profileB: UserProfile = {
  archetype: Archetype.NATURAL,
  verticalRatio: VerticalRatio.SHORT_TORSO_LONG_LEGS,
  horizontalRatio: HorizontalRatio.STRAIGHT,
  valueContrast: ValueContrast.LOW,
  shoulderSlope: ShoulderSlope.ROUNDED,
  neckLength: NeckLength.LONG_THIN,
  jawShape: JawShape.NARROW,
};

const recommendationsB = generateRecommendations(profileB);

console.log("\n=== PROFILE B RECOMMENDATIONS ===");
console.log(JSON.stringify(recommendationsB, null, 2));

/*
Expected output highlights for Profile B:
- Fabrics: textured linen, slubbed cotton, matte flannel, raw denim
- Silhouette: unconstructed jacket, pleated trousers, relaxed fit
  + structured shoulder construction (to correct rounded slope)
  + horizontal detailing to build visual shoulder width (straight drop)
- Trouser rise: MID-TO-LOW (short torso must not be compressed)
- Jacket length: STANDARD OR LONG (extend the torso visually)
- Trouser break: SLIGHT BREAK tolerated (long legs benefit from this)
- Collar: turtleneck, crew neck, mock neck — fill the long neck
           + point collar (narrow jaw)
- Contrast: tonal monochrome (all-navy, earth tones)
- Shoulder: structured/yoke construction — not soft/raglan
- Primary principle: texture and unconstructed relaxed fit
*/

// ---------------------------------------------------------------------------
// GOOGLE AI STUDIO USAGE NOTE
// ---------------------------------------------------------------------------
/*
  To use this engine in Google AI Studio:

  1. Paste the full contents of models.ts, rules_database.ts, engine.ts,
     and output_schema.ts into your system prompt context.

  2. Instruct the model:
     "You are a styling engine. When given a user profile JSON object matching
      the UserProfile interface, call generateRecommendations(profile) and
      return the result as a StyleRecommendation JSON object. Never invent
      rules not present in the rules database. Never recommend specific brands."

  3. Provide user physical measurement data as a UserProfile JSON object.

  4. The model will traverse the decision tree and return a structured
     StyleRecommendation with all five categories populated.
*/
