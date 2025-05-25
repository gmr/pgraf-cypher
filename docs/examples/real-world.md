# Real-world Use Cases

Complete application examples showing PGraf Cypher in production scenarios.

## Social Media Analytics Platform

### User Engagement Dashboard

```python
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pgraf_cypher import PGrafCypher
from pydantic import PostgresDsn

class SocialAnalytics:
    def __init__(self, db_url: PostgresDsn):
        self.cypher = PGrafCypher(db_url)

    async def initialize(self):
        await self.cypher.initialize()

    async def close(self):
        await self.cypher.aclose()

    async def get_user_engagement_metrics(self, user_id: str) -> Dict[str, Any]:
        """Calculate comprehensive user engagement metrics."""

        # Follower growth
        follower_query = """
        MATCH (u:User {id: $user_id})<-[:FOLLOWS]-(follower:User)
        WHERE follower.created_at > datetime() - duration('P30D')
        RETURN COUNT(follower) as new_followers
        """

        # Content performance
        content_query = """
        MATCH (u:User {id: $user_id})-[:POSTED]->(p:Post)
        WHERE p.created_at > datetime() - duration('P30D')
        OPTIONAL MATCH (p)<-[:LIKES]-(liker:User)
        OPTIONAL MATCH (p)<-[:SHARES]-(sharer:User)
        OPTIONAL MATCH (p)<-[:COMMENTS]-(commenter:User)
        RETURN COUNT(DISTINCT p) as posts,
               COUNT(DISTINCT liker) as total_likes,
               COUNT(DISTINCT sharer) as total_shares,
               COUNT(DISTINCT commenter) as total_comments,
               AVG(p.reach) as avg_reach
        """

        # Engagement rate
        engagement_query = """
        MATCH (u:User {id: $user_id})<-[:FOLLOWS]-(follower:User)
        WITH u, COUNT(follower) as follower_count
        MATCH (u)-[:POSTED]->(p:Post)
        WHERE p.created_at > datetime() - duration('P30D')
        OPTIONAL MATCH (p)<-[:LIKES|SHARES|COMMENTS]-(engager:User)
        RETURN follower_count,
               COUNT(DISTINCT p) as posts,
               COUNT(DISTINCT engager) as total_engagements,
               (COUNT(DISTINCT engager) * 1.0 / follower_count) as engagement_rate
        """

        try:
            metrics = {}

            # Execute queries (replacing $user_id with actual value)
            formatted_follower_query = follower_query.replace('$user_id', f'"{user_id}"')
            async with self.cypher.execute(formatted_follower_query) as cursor:
                async for row in cursor:
                    metrics['new_followers'] = row[0]

            formatted_content_query = content_query.replace('$user_id', f'"{user_id}"')
            async with self.cypher.execute(formatted_content_query) as cursor:
                async for row in cursor:
                    metrics.update({
                        'posts': row[0],
                        'total_likes': row[1],
                        'total_shares': row[2],
                        'total_comments': row[3],
                        'avg_reach': row[4] or 0
                    })

            formatted_engagement_query = engagement_query.replace('$user_id', f'"{user_id}"')
            async with self.cypher.execute(formatted_engagement_query) as cursor:
                async for row in cursor:
                    metrics.update({
                        'follower_count': row[0],
                        'engagement_rate': row[3] or 0
                    })

            return metrics

        except Exception as e:
            print(f"Error calculating engagement metrics: {e}")
            return {}

    async def get_trending_content(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Find trending content based on engagement velocity."""

        query = """
        MATCH (p:Post)
        WHERE p.created_at > datetime() - duration('P1D')
        OPTIONAL MATCH (p)<-[:LIKES]-(liker:User)
        OPTIONAL MATCH (p)<-[:SHARES]-(sharer:User)
        OPTIONAL MATCH (p)<-[:COMMENTS]-(commenter:User)
        OPTIONAL MATCH (p)<-[:POSTED]-(author:User)
        WITH p, author,
             COUNT(DISTINCT liker) as likes,
             COUNT(DISTINCT sharer) as shares,
             COUNT(DISTINCT commenter) as comments
        WITH p, author, likes, shares, comments,
             (likes + shares * 3 + comments * 2) as engagement_score,
             duration.inHours(datetime(), p.created_at) as hours_old
        WHERE hours_old > 0
        RETURN p.id, p.title, p.content, author.name,
               likes, shares, comments,
               (engagement_score / hours_old) as velocity_score
        ORDER BY velocity_score DESC
        LIMIT $limit
        """

        try:
            formatted_query = query.replace('$limit', str(limit))
            trending = []

            async with self.cypher.execute(formatted_query) as cursor:
                async for row in cursor:
                    trending.append({
                        'post_id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'author': row[3],
                        'likes': row[4],
                        'shares': row[5],
                        'comments': row[6],
                        'velocity_score': row[7]
                    })

            return trending

        except Exception as e:
            print(f"Error finding trending content: {e}")
            return []

# Usage example
async def run_social_analytics():
    analytics = SocialAnalytics(
        PostgresDsn('postgresql://user:pass@localhost/social_db')
    )

    await analytics.initialize()

    try:
        # Get user metrics
        metrics = await analytics.get_user_engagement_metrics("user123")
        print(f"User engagement: {metrics}")

        # Get trending content
        trending = await analytics.get_trending_content(10)
        print(f"Trending posts: {len(trending)}")

    finally:
        await analytics.close()
```

## E-commerce Recommendation Engine

### Product Recommendation System

```python
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ProductRecommendation:
    product_id: str
    name: str
    category: str
    price: float
    similarity_score: float
    reason: str

class EcommerceRecommendations:
    def __init__(self, db_url: PostgresDsn):
        self.cypher = PGrafCypher(db_url)

    async def initialize(self):
        await self.cypher.initialize()

    async def close(self):
        await self.cypher.aclose()

    async def get_collaborative_recommendations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[ProductRecommendation]:
        """Find products based on similar users' purchases."""

        query = """
        // Find users with similar purchase history
        MATCH (target:User {id: $user_id})-[:PURCHASED]->(item:Product)
        WITH target, COLLECT(item.id) as target_purchases

        MATCH (similar:User)-[:PURCHASED]->(common:Product)
        WHERE common.id IN target_purchases
          AND similar <> target
        WITH target, similar, COUNT(common) as common_purchases,
             SIZE(target_purchases) as target_count
        WHERE common_purchases >= 2

        // Find products similar users bought that target hasn't
        MATCH (similar)-[:PURCHASED]->(recommendation:Product)
        WHERE NOT (target)-[:PURCHASED]->(recommendation)

        WITH recommendation,
             COUNT(DISTINCT similar) as recommender_count,
             AVG(common_purchases * 1.0 / target_count) as similarity_avg

        RETURN recommendation.id, recommendation.name,
               recommendation.category, recommendation.price,
               similarity_avg * recommender_count as score
        ORDER BY score DESC
        LIMIT $limit
        """

        try:
            formatted_query = query.replace('$user_id', f'"{user_id}"').replace('$limit', str(limit))
            recommendations = []

            async with self.cypher.execute(formatted_query) as cursor:
                async for row in cursor:
                    recommendations.append(ProductRecommendation(
                        product_id=row[0],
                        name=row[1],
                        category=row[2],
                        price=float(row[3]),
                        similarity_score=float(row[4]),
                        reason="Users with similar purchases also bought this"
                    ))

            return recommendations

        except Exception as e:
            print(f"Error getting collaborative recommendations: {e}")
            return []

    async def get_category_recommendations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[ProductRecommendation]:
        """Recommend products from frequently purchased categories."""

        query = """
        // Find user's preferred categories
        MATCH (user:User {id: $user_id})-[:PURCHASED]->(p:Product)
        WITH user, p.category as category, COUNT(*) as purchases
        ORDER BY purchases DESC
        LIMIT 3

        // Find highly rated products in those categories
        MATCH (product:Product {category: category})
        WHERE NOT (user)-[:PURCHASED]->(product)
        OPTIONAL MATCH (product)<-[r:RATED]-(rater:User)
        WITH product, category, purchases,
             COUNT(r) as rating_count,
             AVG(r.score) as avg_rating
        WHERE rating_count >= 5 AND avg_rating >= 4.0

        RETURN product.id, product.name, product.category,
               product.price, (purchases * avg_rating) as score
        ORDER BY score DESC
        LIMIT $limit
        """

        try:
            formatted_query = query.replace('$user_id', f'"{user_id}"').replace('$limit', str(limit))
            recommendations = []

            async with self.cypher.execute(formatted_query) as cursor:
                async for row in cursor:
                    recommendations.append(ProductRecommendation(
                        product_id=row[0],
                        name=row[1],
                        category=row[2],
                        price=float(row[3]),
                        similarity_score=float(row[4]),
                        reason=f"Highly rated in your preferred category: {row[2]}"
                    ))

            return recommendations

        except Exception as e:
            print(f"Error getting category recommendations: {e}")
            return []

    async def get_trending_recommendations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[ProductRecommendation]:
        """Recommend currently trending products."""

        query = """
        MATCH (user:User {id: $user_id})
        MATCH (product:Product)
        WHERE NOT (user)-[:PURCHASED]->(product)

        // Calculate trend score based on recent activity
        OPTIONAL MATCH (product)<-[:PURCHASED]-(buyer:User)
        WHERE buyer.purchase_date > datetime() - duration('P7D')

        OPTIONAL MATCH (product)<-[:VIEWED]-(viewer:User)
        WHERE viewer.view_date > datetime() - duration('P1D')

        OPTIONAL MATCH (product)<-[:RATED]-(rater:User)
        WHERE rater.rating_date > datetime() - duration('P7D')
          AND rater.score >= 4

        WITH product,
             COUNT(DISTINCT buyer) as recent_purchases,
             COUNT(DISTINCT viewer) as recent_views,
             COUNT(DISTINCT rater) as recent_good_ratings

        WITH product,
             (recent_purchases * 10 + recent_views + recent_good_ratings * 5) as trend_score
        WHERE trend_score > 0

        RETURN product.id, product.name, product.category,
               product.price, trend_score
        ORDER BY trend_score DESC
        LIMIT $limit
        """

        try:
            formatted_query = query.replace('$user_id', f'"{user_id}"').replace('$limit', str(limit))
            recommendations = []

            async with self.cypher.execute(formatted_query) as cursor:
                async for row in cursor:
                    recommendations.append(ProductRecommendation(
                        product_id=row[0],
                        name=row[1],
                        category=row[2],
                        price=float(row[3]),
                        similarity_score=float(row[4]),
                        reason="Trending now - lots of recent activity"
                    ))

            return recommendations

        except Exception as e:
            print(f"Error getting trending recommendations: {e}")
            return []

# Usage example
async def run_ecommerce_recommendations():
    recommender = EcommerceRecommendations(
        PostgresDsn('postgresql://user:pass@localhost/ecommerce_db')
    )

    await recommender.initialize()

    try:
        user_id = "customer123"

        # Get different types of recommendations
        collaborative = await recommender.get_collaborative_recommendations(user_id, 5)
        category_based = await recommender.get_category_recommendations(user_id, 5)
        trending = await recommender.get_trending_recommendations(user_id, 5)

        print(f"Collaborative: {len(collaborative)} recommendations")
        print(f"Category-based: {len(category_based)} recommendations")
        print(f"Trending: {len(trending)} recommendations")

        # Combine and rank all recommendations
        all_recs = collaborative + category_based + trending
        all_recs.sort(key=lambda x: x.similarity_score, reverse=True)

        print("\\nTop 10 Combined Recommendations:")
        for i, rec in enumerate(all_recs[:10], 1):
            print(f"{i}. {rec.name} (${rec.price:.2f}) - {rec.reason}")

    finally:
        await recommender.close()
```

## Knowledge Management System

### Document Discovery and Expert Finding

```python
class KnowledgeGraph:
    def __init__(self, db_url: PostgresDsn):
        self.cypher = PGrafCypher(db_url)

    async def initialize(self):
        await self.cypher.initialize()

    async def close(self):
        await self.cypher.aclose()

    async def find_experts(self, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find subject matter experts for a given topic."""

        query = """
        // Find documents about the topic
        MATCH (doc:Document)
        WHERE doc.content CONTAINS $topic
           OR doc.title CONTAINS $topic
           OR ANY(tag IN doc.tags WHERE tag CONTAINS $topic)

        // Find authors and contributors
        MATCH (doc)<-[:AUTHORED|CONTRIBUTED|REVIEWED]-(person:Person)

        // Calculate expertise score
        WITH person, doc,
             CASE
               WHEN (person)-[:AUTHORED]->(doc) THEN 3
               WHEN (person)-[:CONTRIBUTED]->(doc) THEN 2
               ELSE 1
             END as contribution_weight

        // Additional signals of expertise
        OPTIONAL MATCH (person)-[:PRESENTED]->(presentation:Presentation)
        WHERE presentation.topic CONTAINS $topic

        OPTIONAL MATCH (person)<-[:MENTIONED]-(mention:Document)
        WHERE mention.content CONTAINS $topic

        WITH person,
             SUM(contribution_weight) as doc_score,
             COUNT(DISTINCT presentation) as presentation_count,
             COUNT(DISTINCT mention) as mention_count

        WITH person,
             (doc_score + presentation_count * 2 + mention_count) as expertise_score
        WHERE expertise_score > 0

        RETURN person.name, person.email, person.department,
               person.title, expertise_score
        ORDER BY expertise_score DESC
        LIMIT $limit
        """

        try:
            formatted_query = query.replace('$topic', f'"{topic}"').replace('$limit', str(limit))
            experts = []

            async with self.cypher.execute(formatted_query) as cursor:
                async for row in cursor:
                    experts.append({
                        'name': row[0],
                        'email': row[1],
                        'department': row[2],
                        'title': row[3],
                        'expertise_score': row[4]
                    })

            return experts

        except Exception as e:
            print(f"Error finding experts: {e}")
            return []

    async def discover_related_content(
        self,
        document_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find documents related to a given document."""

        query = """
        MATCH (source:Document {id: $doc_id})

        // Method 1: Documents with shared tags
        MATCH (related:Document)
        WHERE related <> source
          AND ANY(tag IN source.tags WHERE tag IN related.tags)
        WITH source, related,
             SIZE([tag IN source.tags WHERE tag IN related.tags]) as shared_tags

        // Method 2: Documents by same authors
        OPTIONAL MATCH (source)<-[:AUTHORED]-(author:Person)-[:AUTHORED]->(related)
        WITH source, related, shared_tags,
             COUNT(DISTINCT author) as shared_authors

        // Method 3: Documents cited together
        OPTIONAL MATCH (source)<-[:CITES]-(citing:Document)-[:CITES]->(related)
        WITH source, related, shared_tags, shared_authors,
             COUNT(DISTINCT citing) as co_citations

        // Method 4: Content similarity (simplified)
        WITH source, related, shared_tags, shared_authors, co_citations,
             CASE
               WHEN source.category = related.category THEN 1
               ELSE 0
             END as same_category

        WITH related,
             (shared_tags * 3 + shared_authors * 2 + co_citations * 4 + same_category) as relevance_score
        WHERE relevance_score > 0

        RETURN related.id, related.title, related.summary,
               related.created_at, relevance_score
        ORDER BY relevance_score DESC
        LIMIT $limit
        """

        try:
            formatted_query = query.replace('$doc_id', f'"{document_id}"').replace('$limit', str(limit))
            related_docs = []

            async with self.cypher.execute(formatted_query) as cursor:
                async for row in cursor:
                    related_docs.append({
                        'document_id': row[0],
                        'title': row[1],
                        'summary': row[2],
                        'created_at': row[3],
                        'relevance_score': row[4]
                    })

            return related_docs

        except Exception as e:
            print(f"Error discovering related content: {e}")
            return []

    async def get_knowledge_gaps(self, department: str) -> List[Dict[str, Any]]:
        """Identify knowledge gaps in a department."""

        query = """
        // Find topics that other departments have expertise in
        MATCH (expert:Person)-[:AUTHORED|CONTRIBUTED]->(doc:Document)
        WHERE expert.department <> $dept
        WITH doc.category as topic, COUNT(DISTINCT expert) as external_experts

        // Check if our department has experts in these topics
        OPTIONAL MATCH (internal:Person)-[:AUTHORED|CONTRIBUTED]->(internal_doc:Document)
        WHERE internal.department = $dept
          AND internal_doc.category = topic
        WITH topic, external_experts, COUNT(DISTINCT internal) as internal_experts

        // Identify gaps where we have few/no internal experts
        WHERE external_experts >= 3 AND internal_experts <= 1

        RETURN topic, external_experts, internal_experts,
               (external_experts - internal_experts) as gap_size
        ORDER BY gap_size DESC
        """

        try:
            formatted_query = query.replace('$dept', f'"{department}"')
            gaps = []

            async with self.cypher.execute(formatted_query) as cursor:
                async for row in cursor:
                    gaps.append({
                        'topic': row[0],
                        'external_experts': row[1],
                        'internal_experts': row[2],
                        'gap_size': row[3]
                    })

            return gaps

        except Exception as e:
            print(f"Error identifying knowledge gaps: {e}")
            return []

# Usage example
async def run_knowledge_management():
    kg = KnowledgeGraph(
        PostgresDsn('postgresql://user:pass@localhost/knowledge_db')
    )

    await kg.initialize()

    try:
        # Find machine learning experts
        ml_experts = await kg.find_experts("machine learning", 5)
        print(f"ML Experts: {len(ml_experts)}")

        # Find related documents
        related = await kg.discover_related_content("doc123", 5)
        print(f"Related documents: {len(related)}")

        # Identify knowledge gaps
        gaps = await kg.get_knowledge_gaps("Engineering")
        print(f"Knowledge gaps: {len(gaps)}")

    finally:
        await kg.close()
```

## Performance Monitoring

### Query Performance Tracking

```python
import time
import logging
from dataclasses import dataclass
from typing import Optional

@dataclass
class QueryMetrics:
    query_hash: str
    execution_time: float
    row_count: int
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None

class PerformanceMonitor:
    def __init__(self, cypher: PGrafCypher):
        self.cypher = cypher
        self.metrics: List[QueryMetrics] = []
        self.logger = logging.getLogger(__name__)

    async def execute_with_monitoring(self, query: str) -> List[Any]:
        """Execute query with performance monitoring."""
        query_hash = hash(query)
        start_time = time.time()

        try:
            results = []
            async with self.cypher.execute(query) as cursor:
                async for row in cursor:
                    results.append(row)

            execution_time = time.time() - start_time

            metrics = QueryMetrics(
                query_hash=str(query_hash),
                execution_time=execution_time,
                row_count=len(results),
                timestamp=datetime.now(),
                success=True
            )

            self.metrics.append(metrics)

            if execution_time > 5.0:  # Slow query threshold
                self.logger.warning(f"Slow query detected: {execution_time:.2f}s")

            return results

        except Exception as e:
            execution_time = time.time() - start_time

            metrics = QueryMetrics(
                query_hash=str(query_hash),
                execution_time=execution_time,
                row_count=0,
                timestamp=datetime.now(),
                success=False,
                error_message=str(e)
            )

            self.metrics.append(metrics)
            self.logger.error(f"Query failed: {e}")
            raise

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.metrics:
            return {}

        successful = [m for m in self.metrics if m.success]
        failed = [m for m in self.metrics if not m.success]

        return {
            'total_queries': len(self.metrics),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(self.metrics) * 100,
            'avg_execution_time': sum(m.execution_time for m in successful) / len(successful) if successful else 0,
            'max_execution_time': max((m.execution_time for m in successful), default=0),
            'total_rows_returned': sum(m.row_count for m in successful)
        }
```

These real-world examples demonstrate how to build complete applications using PGraf Cypher, including proper error handling, performance monitoring, and scalable architectures.

## Next Steps

- **[Advanced Queries](../user-guide/advanced-queries.md)** - Optimization techniques
- **[Error Handling](../user-guide/error-handling.md)** - Robust error handling strategies
- **[API Reference](../api/pgraf-cypher.md)** - Complete API documentation
