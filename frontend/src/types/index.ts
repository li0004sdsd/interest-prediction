export interface UserOut {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface BehaviorEventOut {
  id: number;
  category: string;
  action: string;
  weight: number;
  created_at: string;
}

export interface CategoryScore {
  category: string;
  score: number;
  rank: number;
}

export interface InterestTag {
  tag: string;
  confidence: number;
}

export interface PredictionResult {
  user_id: number;
  username: string;
  scores: CategoryScore[];
  tags: InterestTag[];
  total_events: number;
}
