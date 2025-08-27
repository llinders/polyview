
export const APP_TITLE = 'PolyView';
export const APP_SUBTITLE = 'Gaining clarity through diverse perspectives.';

export const ANALYSIS_STEPS = [
  'search_agent',
  'perspective_identification',
  'perspective_clustering',
  'perspective_synthesis',
  'summary_generation',
];

export const formatStepName = (stepName: string) => {
  return stepName
    .replace(/_/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());
};
