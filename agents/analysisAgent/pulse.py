import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

class Calculator:
    def __init__(self, political_bigrams, threshold=0.6):
        """
        Initialize the calculator with political bigrams and similarity threshold.
        """
        self.threshold = threshold
        
        # Prepare bigram data for vectorized operations
        self.bigram_embeddings = np.array([item['embedding'] for item in political_bigrams])
        self.bigram_weights = np.array([item['weight'] for item in political_bigrams])
        self.bigram_categories = [item['category'] for item in political_bigrams]
        self.bigram_subcategories = [item['subcategory'] for item in political_bigrams]
        self.bigram_keywords = [item['keyword'] for item in political_bigrams]

    def _normalize_dict(self, d):
        """
        Normalize a flat dictionary's values to a 0-100 range.
        """
        values = list(d.values())
        if not values:
            return d
        max_val = max(values + [0.01])  # Avoid division by zero
        return {k: min(100, (v / max_val) * 100) for k, v in d.items()}

    def _normalize_nested_dict(self, nested_dict):
        """
        Normalize a nested dictionary's values to a 0-100 range.
        """
        all_values = []
        for date_dict in nested_dict.values():
            all_values.extend(date_dict.values())
        
        if all_values:
            max_val = max(all_values + [0.01])
            for date, items in nested_dict.items():
                nested_dict[date] = {k: min(100, (v / max_val) * 100) for k, v in items.items()}
        return nested_dict

    def calculate(self, articles_dict):
        """
        Calculate political risk scores from article embeddings.
        Returns normalized scores aggregated by date, category, subcategory, and keyword.
        """
        results = {
            'total_by_date': defaultdict(float),
            'category_by_date': defaultdict(lambda: defaultdict(float)),
            'subcategory_by_date': defaultdict(lambda: defaultdict(float)),
            'keyword_by_date': defaultdict(lambda: defaultdict(float))
        }
        
        counts = {
            'category': defaultdict(set),
            'subcategory': defaultdict(set),
            'keyword': defaultdict(set)
        }
        
        for article_title, article_data in articles_dict.items():
            article_embedding = np.array(article_data['embedding']).reshape(1, -1)
            article_date = article_data['date']

            if not isinstance(article_date, str):
                try:
                    article_date = article_date.strftime('%Y-%m-%d')
                except:
                    article_date = str(article_date)

            similarities = cosine_similarity(article_embedding, self.bigram_embeddings)[0]
            matches = np.where(similarities >= self.threshold)[0]

            if len(matches) == 0:
                continue

            for idx in matches:
                score = similarities[idx] * self.bigram_weights[idx]
                category = self.bigram_categories[idx]
                subcategory = self.bigram_subcategories[idx]
                keyword = self.bigram_keywords[idx]

                results['total_by_date'][article_date] += score
                results['category_by_date'][article_date][category] += score
                results['subcategory_by_date'][article_date][subcategory] += score
                results['keyword_by_date'][article_date][keyword] += score

                counts['category'][category].add(article_title)
                counts['subcategory'][subcategory].add(article_title)
                counts['keyword'][keyword].add(article_title)

        # Normalize
        results['total_by_date'] = self._normalize_dict(results['total_by_date'])
        for level in ['category_by_date', 'subcategory_by_date', 'keyword_by_date']:
            results[level] = self._normalize_nested_dict(results[level])

        # Convert defaultdicts to dicts
        return {k: dict(v) if isinstance(v, defaultdict) else v for k, v in results.items()}
