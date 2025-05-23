import logging
import typing

import antlr4

from pgraf_cypher import antlr, to_sql


class PGrafCypher:
    """Add Cypher language support to pgraf"""

    def __init__(self, schema: str = 'pgraf'):
        self._schema = schema

    @staticmethod
    def translate(query: str) -> tuple[str, dict[str, typing.Any]]:
        """
        Parse a Cypher query and translate it to a PostgreSQL query.

        Args:
            query: The Cypher query string

        Returns:
            A SQL Composable object representing the equivalent PostgreSQL
            query
        """
        parser = antlr.Cypher25Parser(
            antlr4.CommonTokenStream(
                antlr.Cypher25Lexer(antlr4.InputStream(query))
            )
        )
        tree = parser.statements()
        walker = antlr4.ParseTreeWalker()
        converter = to_sql.CypherToSQL()
        walker.walk(converter, tree)
        return converter.translate()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    query1 = """\
    MATCH (u1:User {email: "foo@aweber.com"})-[:author]->(m1:SlackMessage)
    MATCH (u2:User {email: "bar@aweber.com"})-[:author]->(m2:SlackMessage)
    WHERE m1.thread_ts = m2.thread_ts
      AND m1 <> m2
      AND NOT EXISTS {
        MATCH (m1)-[:channel]->(:SlackChannel {name: "@privatedm"})
      }
      AND NOT EXISTS {
        MATCH (m2)-[:channel]->(:SlackChannel {name: "@privatedm"})
      }
    RETURN m1, m2
    ORDER BY m1.ts DESC
    LIMIT 100        
    """
    print(PGrafCypher.translate(query1))
