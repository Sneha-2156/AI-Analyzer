export type ClassifiedQuestion = {
  id: string;
  topic: string;
  type: string;
  difficulty: string;
  marks: number | null;
};

export type TopicStats = {
  topic: string;
  frequency: number;
  total_marks: number;
  trend: "increasing" | "decreasing" | "stable";
  score: number;
};

export type StudyPlanDay = {
  day: number;
  topics: string[];
  hours: number;
  focus: string;
};

export type AnalyzePayload = {
  questions: ClassifiedQuestion[];
  topics: TopicStats[];
};
