import type { CheckProfile } from './types.js';

export const ALLOWED_CHECK_PROFILES: CheckProfile[] = [
  'candidate-focused-tests',
  'frontend-type-check',
  'candidate-demo-offline-build',
  'promoted-demo-offline-build',
];

export const REQUIRED_CANDIDATE_PROMOTE_PROFILES: CheckProfile[] = [
  'candidate-focused-tests',
  'frontend-type-check',
  'candidate-demo-offline-build',
];

export function isAllowedProfile(profile: string): profile is CheckProfile {
  return ALLOWED_CHECK_PROFILES.includes(profile as CheckProfile);
}

export function missingCandidatePromoteProfiles(profiles: string[]): CheckProfile[] {
  const profileSet = new Set(profiles);
  return REQUIRED_CANDIDATE_PROMOTE_PROFILES.filter((profile) => !profileSet.has(profile));
}
