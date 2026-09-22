export interface CreateTopicBody {
  name: string;
  subject_id?: string;
  parent_id?: string;
}

export interface UpdateTopicBody {
  name?: string;
}
