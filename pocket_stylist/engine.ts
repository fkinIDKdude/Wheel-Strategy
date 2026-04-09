// =============================================================================
// POCKET STYLIST — LOGIC ENGINE
// The decision tree. Takes a UserProfile and returns a StyleRecommendation.
// This is a pure function with no side effects.
// =============================================================================

import { UserProfile, ShoulderSlope, NeckLength, JawShape } from "./models";
import {
  ARCHETYPE_RULES,
  VERTICAL_RATIO_RULES,
  HORIZONTAL_RATIO_RULES,
  VALUE_CONTRAST_RULES,
  SHOULDER_SLOPE_RULES,
  NECK_LENGTH_RULES,
  JAW_SHAPE_RULES,
} from "./rules_database";
import { StyleRecommendation } from "./output_schema";

// ---------------------------------------------------------------------------
// HELPERS — Merge and deduplicate string arrays
// ---------------------------------------------------------------------------

function mergeUnique(...arrays: string[][]): string[] {
  return [...new Set(arrays.flat())];
}

function subtractAvoids(approved: string[], avoids: string[]): string[] {
  // Remove any approved item that appears in avoids (conflict resolution)
  const avoidSet = new Set(avoids.map((s) => s.toLowerCase()));
  return approved.filter((item) => !avoidSet.has(item.toLowerCase()));
}

// ---------------------------------------------------------------------------
// STEP 1 — Determine primary design principle from archetype
// ---------------------------------------------------------------------------

function getPrimaryDesignPrinciple(profile: UserProfile): string {
  const archetypePrinciples: Record<string, string> = {
    DRAMATIC: "Preserve and extend unbroken vertical lines through long, structured, heavyweight garments.",
    NATURAL: "Allow the body to move freely through unconstructed, textured, matte fabrics with a relaxed fit.",
    ROMANTIC: "Taper and soften the silhouette with draped fabrics that acknowledge the waist.",
    GAMINE: "Deliberately break the vertical line with cropped tailoring and high contrast between top and bottom halves.",
    CLASSIC: "Maintain perfect bilateral symmetry and medium proportions — avoid all extremes.",
  };
  return archetypePrinciples[profile.archetype];
}

// ---------------------------------------------------------------------------
// STEP 2 — Fabric recommendations (archetype + archetype-override rules)
// ---------------------------------------------------------------------------

function buildFabricRecommendation(profile: UserProfile) {
  const archetypeRule = ARCHETYPE_RULES[profile.archetype];

  // Rounded shoulders require structured fabrics — inject this constraint
  const shoulderFabricNote =
    profile.shoulderSlope === ShoulderSlope.ROUNDED
      ? "Structured or canvas-fused fabrics are preferred to correct shoulder slope."
      : null;

  const primaryNotes = [
    ...archetypeRule.notes.slice(0, 1), // Top archetype note
    ...(shoulderFabricNote ? [shoulderFabricNote] : []),
  ];

  return {
    approved: archetypeRule.fabric.approved,
    avoid: archetypeRule.fabric.avoid,
    primaryNotes,
  };
}

// ---------------------------------------------------------------------------
// STEP 3 — Silhouette recommendations (archetype + horizontal ratio override)
// ---------------------------------------------------------------------------

function buildSilhouetteRecommendation(profile: UserProfile) {
  const archetypeRule = ARCHETYPE_RULES[profile.archetype];
  const horizontalRule = HORIZONTAL_RATIO_RULES[profile.horizontalRatio];

  // Merge approved, resolve conflicts with avoids
  const mergedApproved = mergeUnique(
    archetypeRule.silhouette.approved,
    horizontalRule.approved
  );
  const mergedAvoid = mergeUnique(
    archetypeRule.silhouette.avoid,
    horizontalRule.avoid
  );
  const finalApproved = subtractAvoids(mergedApproved, mergedAvoid);

  const primaryNotes = [
    horizontalRule.strategy,
    ...archetypeRule.notes.slice(1), // Remaining archetype notes
  ];

  return {
    approved: finalApproved,
    avoid: mergedAvoid,
    primaryNotes,
  };
}

// ---------------------------------------------------------------------------
// STEP 4 — Proportion and break rules (vertical ratio + shoulder + collar)
// ---------------------------------------------------------------------------

function buildProportionRecommendation(profile: UserProfile) {
  const vertRule = VERTICAL_RATIO_RULES[profile.verticalRatio];
  const shoulderRule = SHOULDER_SLOPE_RULES[profile.shoulderSlope];
  const neckRule = NECK_LENGTH_RULES[profile.neckLength];
  const jawRule = JAW_SHAPE_RULES[profile.jawShape];

  // Merge collar approved: intersection of what neck AND jaw allow
  // (Both must agree. If jaw says "spread" but neck says "avoid wide", neck wins for SHORT_THICK.)
  const mergedCollarApproved = mergeUnique(
    neckRule.collarTypes.approved,
    jawRule.collarTypes.approved
  );
  const mergedCollarAvoid = mergeUnique(
    neckRule.collarTypes.avoid,
    jawRule.collarTypes.avoid
  );
  const finalCollarApproved = subtractAvoids(mergedCollarApproved, mergedCollarAvoid);

  return {
    trouserRise: vertRule.trouserRise,
    jacketLength: vertRule.jacketLength,
    trouserBreak: vertRule.trouserBreak,
    hemlineGuidance: vertRule.hemlineGuidance,
    shoulderConstruction:
      shoulderRule.approved[0] ??
      "Standard set-in sleeve with natural shoulder.",
    collarApproved: finalCollarApproved,
    collarAvoid: mergedCollarAvoid,
  };
}

// ---------------------------------------------------------------------------
// STEP 5 — Contrast strategy
// ---------------------------------------------------------------------------

function buildContrastRecommendation(profile: UserProfile) {
  return VALUE_CONTRAST_RULES[profile.valueContrast];
}

// ---------------------------------------------------------------------------
// STEP 6 — Build the consolidated "Strictly Avoid" list
// ---------------------------------------------------------------------------

function buildStrictlyAvoid(profile: UserProfile) {
  const archetypeRule = ARCHETYPE_RULES[profile.archetype];
  const horizontalRule = HORIZONTAL_RATIO_RULES[profile.horizontalRatio];
  const contrastRule = VALUE_CONTRAST_RULES[profile.valueContrast];
  const neckRule = NECK_LENGTH_RULES[profile.neckLength];
  const jawRule = JAW_SHAPE_RULES[profile.jawShape];
  const shoulderRule = SHOULDER_SLOPE_RULES[profile.shoulderSlope];

  return {
    fabrics: archetypeRule.fabric.avoid,
    silhouettes: mergeUnique(
      archetypeRule.silhouette.avoid,
      horizontalRule.avoid,
      shoulderRule.avoid
    ),
    collarTypes: mergeUnique(
      neckRule.collarTypes.avoid,
      jawRule.collarTypes.avoid
    ),
    proportionMistakes: [
      // Neck-specific hard rules
      ...(profile.neckLength === NeckLength.SHORT_THICK
        ? [
            "HIGH PRIORITY: Never wear closed crew necks or turtlenecks. They visually eliminate the neck.",
          ]
        : []),
      ...neckRule.avoid,
    ],
    colorMistakes: contrastRule.avoid,
  };
}

// ---------------------------------------------------------------------------
// MASTER FUNCTION — Entry point
// ---------------------------------------------------------------------------

export function generateRecommendations(profile: UserProfile): StyleRecommendation {
  return {
    profileSummary: {
      archetype: profile.archetype,
      verticalRatio: profile.verticalRatio,
      horizontalRatio: profile.horizontalRatio,
      valueContrast: profile.valueContrast,
      shoulderSlope: profile.shoulderSlope,
      neckLength: profile.neckLength,
      jawShape: profile.jawShape,
    },
    approvedFabrics: buildFabricRecommendation(profile),
    requiredFitAndSilhouette: buildSilhouetteRecommendation(profile),
    proportionsAndBreaks: buildProportionRecommendation(profile),
    contrastStrategy: buildContrastRecommendation(profile),
    strictlyAvoid: buildStrictlyAvoid(profile),
    primaryDesignPrinciple: getPrimaryDesignPrinciple(profile),
  };
}
