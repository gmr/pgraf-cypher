import json
import re
import subprocess
import unittest

import pydantic

import pgraf_cypher


class CypherTestCase(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.cypher = pgraf_cypher.PGrafCypher(url=postgres_url())

    async def asyncSetUp(self) -> None:
        await self.cypher.initialize()

    def test_nodes(self) -> None:
        query = """\
        MATCH (n)
        """
        result, properties = self.cypher.translate(query)
        self.assertEqual(result, 'SELECT "n".* FROM "pgraf"."nodes" AS "n"')
        self.assertDictEqual(properties, {})

    def test_nodes_with_label(self) -> None:
        query = """\
        MATCH (n:Person)
        """
        expectation = re.sub(
            r'\s+',
            ' ',
            """SELECT "n".* 
                 FROM "pgraf"."nodes" AS "n" 
                WHERE "n"."labels" = ANY(%(p0)s)""",
        )
        result, properties = self.cypher.translate(query)
        self.assertEqual(result, expectation)
        self.assertDictEqual(properties, {'p0': 'Person'})

    def test_node_with_properties(self) -> None:
        query = """\
        MATCH (n {name: "John"})
        """
        expectation = re.sub(
            r'\s+',
            ' ',
            """SELECT "n".*
                 FROM "pgraf"."nodes" AS "n" 
                WHERE "n"."properties"->>'name' = %(p0)s""",
        )
        result, parameters = self.cypher.translate(query)
        self.assertEqual(result, expectation)
        self.assertDictEqual(parameters, {'p0': 'John'})

    def test_variable_length_paths(self):
        query = """\
        MATCH (a)-[r:KNOWS*1..5]->(b)
        """
        expectation = re.sub(
            r'\s+',
            ' ',
            """WITH RECURSIVE path AS (
                SELECT n1.id AS start_id,
                       n2.id AS end_id,
                       ARRAY[e.source, e.target] AS path_nodes,
                       ARRAY[e.label] AS edge_labels,
                       1 AS depth
                  FROM pgraf.nodes n1
                  JOIN pgraf.edges e ON n1.id = e.source
                  JOIN pgraf.nodes n2 ON e.target = n2.id
                 WHERE e.labels && ARRAY[%(p0)s]
                 UNION ALL
                SELECT p.start_id,
                       n2.id AS end_id,
                       p.path_nodes || n2.id,
                       p.edge_labels || e.label,
                       p.depth + 1
                  FROM path p
                  JOIN pgraf.edges e ON p.end_id = e.source
                  JOIN pgraf.nodes n2 ON e.target = n2.id
                 WHERE p.depth < 5
                   AND e.labels && ARRAY[%(p0)s]
                   AND NOT n2.id = ANY(p.path_nodes) -- Prevent cycles
            )
            SELECT a.id AS a_id,
                   a.properties AS a_properties,
                   b.id AS b_id,
                   b.properties AS b_properties,
                   p.path_nodes,
                   p.edge_labels,
                   p.depth
              FROM path p
              JOIN pgraf.nodes a ON p.start_id = a.id
              JOIN pgraf.nodes b ON p.end_id = b.id
          ORDER BY p.depth""",
        )
        result, parameters = self.cypher.translate(query)
        self.assertEqual(result, expectation)
        self.assertDictEqual(parameters, {'p0': 'KNOWS'})

    def test_bidirectional_relationships(self):
        query = """\
        MATCH (a)-[r:KNOWS]-(b)
        """
        expectation = re.sub(
            r'\s+',
            ' ',
            """SELECT n1.id AS a_id,
                      n1.properties AS a_properties,
                      n2.id AS b_id,
                      n2.properties AS b_properties,
                      e.label AS relationship_label,
                      e.properties AS relationship_properties
                 FROM "pgraf"."nodes" n1
                 JOIN "pgraf"."edges" e
                   ON n1.id = e.source OR n1.id = e.target
                 JOIN "pgraf"."nodes" n2
                   ON (e.target = n2.id  AND e.source = n1.id)
                   OR (e.source = n2.id AND e.target = n1.id)
                WHERE e.labels && ARRAY[%(p0)s]
                  AND n1.id <> n2.id""",
        )
        result, parameters = self.cypher.translate(query)
        self.assertEqual(result, expectation)
        self.assertDictEqual(parameters, {'p0': 'KNOWS'})

    def test_multiple_relationships(self):
        query = """\
        MATCH (a)-[:KNOWS|:FOLLOWS]->(b)
        """
        expectation = re.sub(
            r'\s+',
            ' ',
            """SELECT n1.id AS a_id,
                   n1.properties AS a_properties,
                   n2.id AS b_id,
                   n2.properties AS b_properties,
                   e.labels AS relationship_labels,
                   e.properties AS relationship_properties
              FROM "pgraf"."nodes" n1
              JOIN "pgraf"."edges" e ON n1.id = e.source
              JOIN "pgraf"."nodes" n2 ON e.target = n2.id
             WHERE (e.labels && ARRAY[%(p0)s] OR e.lables && ARRAY[%(p1)s])
               AND n1.id <> n2.id""",
        )
        result, parameters = self.cypher.translate(query)
        self.assertEqual(result, expectation)
        self.assertDictEqual(parameters, {'p0': 'KNOWS', 'p1': 'FOLLOWS'})

    def test_parenthesized_patterns(self):
        query = """\
        MATCH ((a)-[:KNOWS]->(b))<-[:WORKS_WITH]-(c)
        """
        expectation = re.sub(
            r'\s+',
            ' ',
            """SELECT a.id AS a_id,
                   a.properties AS a_properties,
                   b.id AS b_id,
                   b.properties AS b_properties,
                   c.id AS c_id,
                   c.properties AS c_properties,
                   e1.labels AS a_to_b_relationship,
                   e2.labels AS c_to_b_relationship
              FROM "pgraf"."nodes" a
              JOIN "pgraf"."edges" e1 ON a.id = e1.source
              JOIN "pgraf"."nodes" b ON e1.target = b.id
              JOIN "pgraf"."edges" e2 ON b.id = e2.target
              JOIN "pgraf"."nodes" c ON e2.source = c.id
             WHERE e1.labels && ARRAY[%(p0)s]
               AND e2.labels && ARRAY[%(p1)s]
               AND a.id <> b.id
               AND b.id <> c.id
               AND a.id <> c.id""",
        )
        result, parameters = self.cypher.translate(query)
        self.assertEqual(result, expectation)
        self.assertDictEqual(parameters, {'p0': 'KNOWS', 'p1': 'WORKS_WITH'})

    def test_pattern_qualifiers(self):
        query = """\
        MATCH ((a)-[:KNOWS]->(b)){1,3}
        """
        expectation = re.sub(
            r'\s+',
            ' ',
            """WITH RECURSIVE path AS (
                SELECT a.id AS a_id,
                       b.id AS b_id,
                       a.properties AS a_properties,
                       b.properties AS b_properties,
                       ARRAY[a.id, b.id] AS node_path,
                       1 AS path_length
                  FROM "pgraf"."nodes" a
                  JOIN "pgraf"."edges" e ON a.id = e.source
                  JOIN "pgraf"."nodes" b ON e.target = b.id
                 WHERE e.labels && ARRAY[%(p0)s]
                 UNION ALL
                SELECT p.a_id,
                       next_node.id AS b_id,
                       p.a_properties,
                       next_node.properties AS b_properties,
                       p.node_path || next_node.id,
                       p.path_length + 1
                  FROM path p
                  JOIN "pgraf".edges" e ON p.b_id = e.source
                  JOIN "pgraf".nodes" next_node ON e.target = next_node.id
                 WHERE p.path_length < 3
                    AND e.labels && ARRAY[%(p0)s]
                    AND NOT next_node.id = ANY(p.node_path) -- Prevent cycles
            )
            SELECT a_id,
                   b_id,
                   a_properties,
                   b_properties,
                   node_path,
                   path_length
              FROM path
             WHERE path_length BETWEEN 1 AND 3
          ORDER BY path_length""",
        )
        result, parameters = self.cypher.translate(query)
        self.assertEqual(result, expectation)
        self.assertDictEqual(parameters, {'p0': 'KNOWS'})

    def test_shortest_path(self):
        query = """\
        SHORTEST_PATH((a)-[:KNOWS*]-(b))
        """
        expectation = re.sub(
            r'\s+',
            ' ',
            """WITH RECURSIVE shortest_path AS (
                SELECT a.id AS start_id,
                       b.id AS end_id,
                       ARRAY[a.id, b.id] AS path_nodes,
                       ARRAY[e.label] AS edge_labels,
                       1 AS path_length
                  FROM "pgraf"."nodes" a
                  JOIN "pgraf"."edges" e
                    ON (a.id = e.source OR a.id = e.target)
                  JOIN "pgraf"."nodes" b
                    ON (e.target = b.id AND e.source = a.id)
                    OR (e.source = b.id AND e.target = a.id)
                 WHERE e.labels && ARRAY[%(p0)s]
                   AND a.id <> b.id
                 UNION ALL
                SELECT sp.start_id,
                       next_node.id AS end_id,
                       sp.path_nodes || next_node.id,
                       sp.edge_labels || e.label,
                       sp.path_length + 1
                  FROM shortest_path sp
                  JOIN "pgraf"."edges" e
                    ON ARRAY[sp.path_nodes[array_length(sp.path_nodes, 1)]] = ARRAY[e.source]
                    OR ARRAY[sp.path_nodes[array_length(sp.path_nodes, 1)]] = ARRAY[e.target]
                  JOIN "pgraf"."nodes" next_node
                    ON (e.target = next_node.id AND e.source = sp.path_nodes[array_length(sp.path_nodes, 1)])
                    OR (e.source = next_node.id AND e.target = sp.path_nodes[array_length(sp.path_nodes, 1)])
                 WHERE e.labels && ARRAY[%(p0)s]
                   AND NOT next_node.id = ANY(sp.path_nodes) -- Prevent cycles
                   AND sp.path_length < 10),
            shortest_paths_by_pair AS (
                SELECT start_id,
                       end_id,
                       MIN(path_length) AS min_path_length
                  FROM shortest_path
              GROUP BY start_id, end_id)
            SELECT start_n.id AS a_id,
                   start_n.properties AS a_properties,
                   end_n.id AS b_id,
                   end_n.properties AS b_properties,
                   sp.path_nodes,
                   sp.edge_labels,
                   sp.path_length
              FROM shortest_path sp
              JOIN shortest_paths_by_pair spp
                ON sp.start_id = spp.start_id
               AND sp.end_id = spp.end_id
               AND sp.path_length = spp.min_path_length
              JOIN pgraf.nodes start_n
                ON sp.start_id = start_n.id
              JOIN pgraf.nodes end_n
                ON sp.end_id = end_n.id
          ORDER BY sp.path_length""",
        )
        result, parameters = self.cypher.translate(query)
        self.assertEqual(result, expectation)
        self.assertDictEqual(parameters, {'p0': 'KNOWS'})


def _docker_port() -> int:
    result = subprocess.run(  # noqa: S603
        ['docker', 'compose', 'ps', '--format', 'json', 'postgres'],  # noqa: S607
        capture_output=True,
    )
    process = json.loads(result.stdout)
    return process['Publishers'][0]['PublishedPort']



def postgres_url() -> pydantic.PostgresDsn:
    """Return connection parameters for database in either environment"""
    return pydantic.PostgresDsn(
        f'postgres://postgres:password@localhost:{_docker_port()}/postgres'
    )
