// =============================================================================
// POCKET STYLIST — OUTPUT SCHEMA
// The shape of every recommendation object returned to the frontend.
// No brand names are ever included in any field.
// =============================================================================

export interface FabricRecommendation {
  approved: string[];
  avoid: string[];
  primaryNotes: string[];  // e.g. "Weight is more important than fiber for your archetype"
}

export interface SilhouetteRecommendation {
  approved: string[];
  avoid: string[];
  primaryNotes: string[];
}

export interface ProportionRecommendation {
  trouserRise: string;
  jacketLength: string;
  trouserBreak: string;
  hemlineGuidance: string;
  shoulderConstruction: string;
  collarApproved: string[];
  collarAvoid: string[];
}

export interface ContrastRecommendation {
  strategy: string;
  approvedPalettes: string[];
  avoid: string[];
}

export interface AvoidList {
  fabrics: string[];
  silhouettes: string[];
  collarTypes: string[];
  proportionMistakes: string[];
  colorMistakes: string[];
}

export interface StyleRecommendation {
  profileSummary: {
    archetype: string;
    verticalRatio: string;
    horizontalRatio: string;
    valueContrast: string;
    shoulderSlope: string;
    neckLength: string;
    jawShape: string;
  };
  approvedFabrics: FabricRecommendation;
  requiredFitAndSilhouette: SilhouetteRecommendation;
  proportionsAndBreaks: ProportionRecommendation;
  contrastStrategy: ContrastRecommendation;
  strictlyAvoid: AvoidList;
  primaryDesignPrinciple: string;  // The single most important rule for this profile
}
