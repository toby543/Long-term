export type Category =
  | 'Curries & Mains'
  | 'Rice & Breads'
  | 'Snacks & Starters'
  | 'Sweets & Desserts'
  | 'Beverages';

export type Diet = 'veg' | 'egg' | 'non-veg';

export interface Recipe {
  id: string;
  name: string;
  konkaniName?: string;
  category: Category;
  diet: Diet;
  description: string;
  prepTime: string;
  cookTime: string;
  servings: string;
  spiceLevel: 1 | 2 | 3 | 4 | 5;
  ingredients: string[];
  steps: string[];
  tags: string[];
}
