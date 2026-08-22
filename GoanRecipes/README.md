# Goan Kitchen 🍛

A cross-platform (iOS + Android) mobile app built with [Expo](https://expo.dev) / React Native,
showcasing 28 authentic Goan recipes across curries, rice & breads, snacks, sweets, and beverages.

## Features

- Browse recipes by category (Curries & Mains, Rice & Breads, Snacks & Starters, Sweets & Desserts, Beverages)
- Search by name, ingredient, or tag
- Full recipe detail screen: ingredients, step-by-step method, prep/cook time, servings, spice level, diet type
- Save favorites locally on-device (offline, via AsyncStorage) — no account or internet required
- Works fully offline; all recipe data is bundled with the app

## Tech stack

- Expo SDK 51 / React Native 0.74
- TypeScript
- React Navigation (bottom tabs + native stack)
- AsyncStorage for persisted favorites

## Getting started

```bash
cd GoanRecipes
npm install
npx expo start
```

Then:
- Press `i` to open in the iOS Simulator (macOS only), or `a` for an Android emulator
- Or scan the QR code with the **Expo Go** app on your own iPhone/Android phone

## Building for app stores

Use [EAS Build](https://docs.expo.dev/build/introduction/) to produce a real iOS `.ipa` or Android `.aab`:

```bash
npm install -g eas-cli
eas build --platform ios
eas build --platform android
```

## Project structure

```
App.tsx                        # App entry, wraps navigation + favorites provider
src/
  types.ts                     # Recipe/category type definitions
  theme.ts                     # Color palette
  data/recipes.ts              # All 28 Goan recipes (the recipe database)
  context/FavoritesContext.tsx # Favorites state + AsyncStorage persistence
  navigation/RootNavigator.tsx # Tab + stack navigation
  screens/                     # Home, Favorites, RecipeDetail screens
  components/                  # RecipeCard, SearchBar, CategoryChip
```

## Adding more recipes

Add a new object to the `recipes` array in `src/data/recipes.ts` following the existing `Recipe` shape
in `src/types.ts` — no other code changes are needed, the list, search, and detail screens all read from
this single file.
