import type {
  TestInfoOut,
  QuestionOut,
  SubmitTestIn,
  TestResultOut,
} from "@harmony/types";
import { get, post } from "../client";

export const assessmentApi = {
  /** List all active tests */
  getCatalogue: () => get<TestInfoOut[]>("/assessments/catalogue"),

  /** Get questions for a specific test */
  getQuestions: (testId: number) =>
    get<QuestionOut[]>(`/assessments/tests/${testId}/questions`),

  /** Submit a completed test */
  submit: (body: SubmitTestIn) =>
    post<TestResultOut>("/assessments/submit", body),

  /** Get all results for the current candidate */
  getMyResults: () => get<TestResultOut[]>("/assessments/results/me"),

  /** Get results for a specific candidate (employer/manager view) */
  getResultsForCandidate: (crewProfileId: number) =>
    get<TestResultOut[]>(`/assessments/results/${crewProfileId}`),
};
