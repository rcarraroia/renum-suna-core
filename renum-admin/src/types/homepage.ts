export interface TypewriterPhrase {
  id: string;
  text: string;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TypewriterPhraseFormData {
  text: string;
  display_order: number;
  is_active: boolean;
}