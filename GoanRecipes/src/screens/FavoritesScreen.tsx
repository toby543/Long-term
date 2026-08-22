import React, { useMemo } from 'react';
import { FlatList, SafeAreaView, StyleSheet, Text, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { recipes } from '../data/recipes';
import { colors } from '../theme';
import RecipeCard from '../components/RecipeCard';
import { useFavorites } from '../context/FavoritesContext';
import { RootStackParamList } from '../navigation/RootNavigator';

type Props = NativeStackScreenProps<RootStackParamList, 'Favorites'>;

export default function FavoritesScreen({ navigation }: Props) {
  const { favorites } = useFavorites();

  const favRecipes = useMemo(
    () => recipes.filter((r) => favorites.includes(r.id)),
    [favorites]
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.headerBlock}>
        <Text style={styles.appTitle}>My Favorites</Text>
        <Text style={styles.appSubtitle}>
          {favRecipes.length ? `${favRecipes.length} saved recipe${favRecipes.length > 1 ? 's' : ''}` : 'Nothing saved yet'}
        </Text>
      </View>
      <FlatList
        data={favRecipes}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <RecipeCard recipe={item} onPress={() => navigation.navigate('RecipeDetail', { id: item.id })} />
        )}
        ListEmptyComponent={
          <Text style={styles.empty}>Tap the ♡ on any recipe to save it here.</Text>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  headerBlock: { paddingHorizontal: 16, paddingTop: 12, marginBottom: 8 },
  appTitle: { fontSize: 28, fontWeight: '800', color: colors.primaryDark },
  appSubtitle: { fontSize: 13, color: colors.subtext, marginTop: 2 },
  list: { paddingHorizontal: 16, paddingBottom: 24 },
  empty: { textAlign: 'center', color: colors.subtext, marginTop: 60, paddingHorizontal: 30 },
});
