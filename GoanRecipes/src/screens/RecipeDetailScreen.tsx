import React from 'react';
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { recipes } from '../data/recipes';
import { colors, categoryColors } from '../theme';
import { useFavorites } from '../context/FavoritesContext';
import { RootStackParamList } from '../navigation/RootNavigator';

type Props = NativeStackScreenProps<RootStackParamList, 'RecipeDetail'>;

const dietLabel: Record<string, string> = {
  veg: '🌱 Vegetarian',
  egg: '🥚 Contains egg',
  'non-veg': '🍖 Non-vegetarian',
};

export default function RecipeDetailScreen({ route, navigation }: Props) {
  const recipe = recipes.find((r) => r.id === route.params.id);
  const { isFavorite, toggleFavorite } = useFavorites();

  if (!recipe) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.missing}>Recipe not found.</Text>
      </SafeAreaView>
    );
  }

  const fav = isFavorite(recipe.id);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={[styles.banner, { backgroundColor: categoryColors[recipe.category] }]}>
          <Pressable onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Text style={styles.backText}>‹ Back</Text>
          </Pressable>
          <Text style={styles.bannerCategory}>{recipe.category}</Text>
          <Text style={styles.bannerTitle}>{recipe.name}</Text>
          {recipe.konkaniName ? <Text style={styles.bannerSubtitle}>{recipe.konkaniName}</Text> : null}
        </View>

        <View style={styles.body}>
          <View style={styles.metaRow}>
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>Prep</Text>
              <Text style={styles.metaValue}>{recipe.prepTime}</Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>Cook</Text>
              <Text style={styles.metaValue}>{recipe.cookTime}</Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>Serves</Text>
              <Text style={styles.metaValue}>{recipe.servings}</Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>Spice</Text>
              <Text style={styles.metaValue}>{'🌶'.repeat(recipe.spiceLevel)}</Text>
            </View>
          </View>

          <Text style={styles.diet}>{dietLabel[recipe.diet]}</Text>
          <Text style={styles.description}>{recipe.description}</Text>

          <Pressable style={styles.favBtn} onPress={() => toggleFavorite(recipe.id)}>
            <Text style={styles.favBtnText}>{fav ? '♥ Remove from favorites' : '♡ Add to favorites'}</Text>
          </Pressable>

          <Text style={styles.sectionTitle}>Ingredients</Text>
          {recipe.ingredients.map((ing, idx) => (
            <View key={idx} style={styles.bulletRow}>
              <Text style={styles.bullet}>•</Text>
              <Text style={styles.bulletText}>{ing}</Text>
            </View>
          ))}

          <Text style={styles.sectionTitle}>Method</Text>
          {recipe.steps.map((step, idx) => (
            <View key={idx} style={styles.stepRow}>
              <View style={styles.stepNumberCircle}>
                <Text style={styles.stepNumber}>{idx + 1}</Text>
              </View>
              <Text style={styles.stepText}>{step}</Text>
            </View>
          ))}

          <View style={styles.tagsRow}>
            {recipe.tags.map((t) => (
              <View key={t} style={styles.tag}>
                <Text style={styles.tagText}>{t}</Text>
              </View>
            ))}
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  scroll: { paddingBottom: 40 },
  missing: { padding: 24, textAlign: 'center', color: colors.subtext },
  banner: {
    paddingTop: 60,
    paddingBottom: 24,
    paddingHorizontal: 20,
  },
  backBtn: { marginBottom: 16 },
  backText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  bannerCategory: {
    color: 'rgba(255,255,255,0.85)',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  bannerTitle: { color: '#fff', fontSize: 28, fontWeight: '800', marginTop: 4 },
  bannerSubtitle: { color: 'rgba(255,255,255,0.85)', fontSize: 15, fontStyle: 'italic', marginTop: 2 },
  body: { padding: 20 },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: colors.card,
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: 16,
  },
  metaItem: { alignItems: 'center', flex: 1 },
  metaLabel: { fontSize: 11, color: colors.subtext, textTransform: 'uppercase' },
  metaValue: { fontSize: 14, fontWeight: '700', color: colors.text, marginTop: 4 },
  diet: { fontSize: 14, fontWeight: '600', color: colors.text, marginBottom: 8 },
  description: { fontSize: 15, color: colors.subtext, lineHeight: 22, marginBottom: 16 },
  favBtn: {
    borderWidth: 1.5,
    borderColor: colors.primary,
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
    marginBottom: 20,
  },
  favBtnText: { color: colors.primary, fontWeight: '700', fontSize: 15 },
  sectionTitle: { fontSize: 19, fontWeight: '800', color: colors.text, marginTop: 10, marginBottom: 10 },
  bulletRow: { flexDirection: 'row', marginBottom: 6, paddingRight: 10 },
  bullet: { color: colors.primary, marginRight: 8, fontSize: 15 },
  bulletText: { flex: 1, color: colors.text, fontSize: 14, lineHeight: 20 },
  stepRow: { flexDirection: 'row', marginBottom: 14, alignItems: 'flex-start' },
  stepNumberCircle: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    marginTop: 1,
  },
  stepNumber: { color: '#fff', fontSize: 12, fontWeight: '700' },
  stepText: { flex: 1, color: colors.text, fontSize: 14, lineHeight: 21 },
  tagsRow: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 12, gap: 8 },
  tag: { backgroundColor: colors.chipBg, borderRadius: 12, paddingHorizontal: 10, paddingVertical: 5 },
  tagText: { fontSize: 12, color: colors.primaryDark, fontWeight: '600' },
});
