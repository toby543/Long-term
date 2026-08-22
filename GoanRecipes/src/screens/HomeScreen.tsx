import React, { useMemo, useState } from 'react';
import { FlatList, SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { recipes, categories } from '../data/recipes';
import { colors } from '../theme';
import RecipeCard from '../components/RecipeCard';
import SearchBar from '../components/SearchBar';
import CategoryChip from '../components/CategoryChip';
import { RootStackParamList } from '../navigation/RootNavigator';

type Props = NativeStackScreenProps<RootStackParamList, 'Home'>;

export default function HomeScreen({ navigation }: Props) {
  const [query, setQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return recipes.filter((r) => {
      const matchesCategory = activeCategory ? r.category === activeCategory : true;
      if (!matchesCategory) return false;
      if (!q) return true;
      return (
        r.name.toLowerCase().includes(q) ||
        r.konkaniName?.toLowerCase().includes(q) ||
        r.description.toLowerCase().includes(q) ||
        r.tags.some((t) => t.toLowerCase().includes(q)) ||
        r.ingredients.some((i) => i.toLowerCase().includes(q))
      );
    });
  }, [query, activeCategory]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.headerBlock}>
        <Text style={styles.appTitle}>Goan Kitchen</Text>
        <Text style={styles.appSubtitle}>{recipes.length} authentic recipes from Goa</Text>
      </View>
      <View style={styles.searchBlock}>
        <SearchBar value={query} onChange={setQuery} />
      </View>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.chipsRow}
        contentContainerStyle={{ paddingHorizontal: 16 }}
      >
        <CategoryChip label="All" active={activeCategory === null} onPress={() => setActiveCategory(null)} />
        {categories.map((c) => (
          <CategoryChip
            key={c}
            label={c}
            active={activeCategory === c}
            onPress={() => setActiveCategory(activeCategory === c ? null : c)}
          />
        ))}
      </ScrollView>
      <FlatList
        data={filtered}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <RecipeCard recipe={item} onPress={() => navigation.navigate('RecipeDetail', { id: item.id })} />
        )}
        ListEmptyComponent={
          <Text style={styles.empty}>No recipes match your search.</Text>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  headerBlock: { paddingHorizontal: 16, paddingTop: 12 },
  appTitle: { fontSize: 28, fontWeight: '800', color: colors.primaryDark },
  appSubtitle: { fontSize: 13, color: colors.subtext, marginTop: 2, marginBottom: 8 },
  searchBlock: { paddingHorizontal: 16 },
  chipsRow: { marginBottom: 8, flexGrow: 0 },
  list: { paddingHorizontal: 16, paddingBottom: 24 },
  empty: { textAlign: 'center', color: colors.subtext, marginTop: 40 },
});
