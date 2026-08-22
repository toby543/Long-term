import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Recipe } from '../types';
import { colors, categoryColors } from '../theme';
import { useFavorites } from '../context/FavoritesContext';

const dietEmoji: Record<string, string> = {
  veg: '🌱',
  egg: '🥚',
  'non-veg': '🍖',
};

interface Props {
  recipe: Recipe;
  onPress: () => void;
}

export default function RecipeCard({ recipe, onPress }: Props) {
  const { isFavorite, toggleFavorite } = useFavorites();
  const fav = isFavorite(recipe.id);

  return (
    <Pressable style={styles.card} onPress={onPress}>
      <View style={styles.header}>
        <View style={[styles.dot, { backgroundColor: categoryColors[recipe.category] }]} />
        <Text style={styles.category}>{recipe.category}</Text>
        <Pressable hitSlop={10} onPress={() => toggleFavorite(recipe.id)}>
          <Text style={styles.heart}>{fav ? '♥' : '♡'}</Text>
        </Pressable>
      </View>
      <Text style={styles.title}>{recipe.name}</Text>
      {recipe.konkaniName ? <Text style={styles.subtitle}>{recipe.konkaniName}</Text> : null}
      <Text style={styles.description} numberOfLines={2}>
        {recipe.description}
      </Text>
      <View style={styles.footer}>
        <Text style={styles.meta}>{dietEmoji[recipe.diet]} {recipe.diet}</Text>
        <Text style={styles.meta}>⏱ {recipe.cookTime}</Text>
        <Text style={styles.meta}>🌶 {'•'.repeat(recipe.spiceLevel)}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: 16,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.border,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  category: {
    flex: 1,
    fontSize: 12,
    fontWeight: '600',
    color: colors.subtext,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  heart: {
    fontSize: 20,
    color: colors.primary,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text,
  },
  subtitle: {
    fontSize: 13,
    color: colors.subtext,
    fontStyle: 'italic',
    marginBottom: 4,
  },
  description: {
    fontSize: 13,
    color: colors.subtext,
    marginTop: 4,
    lineHeight: 18,
  },
  footer: {
    flexDirection: 'row',
    marginTop: 10,
    gap: 14,
  },
  meta: {
    fontSize: 12,
    color: colors.text,
  },
});
