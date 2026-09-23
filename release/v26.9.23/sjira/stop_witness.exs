# Stop-query witness for GC-CE-26.9.23 (lane CE-INTAKE, wave CE0).
#
# Evaluates the root sj:stopQuery of release/v26.9.23/sjira/goal.ttl exactly
# the way xaas `mix xaas.stop_court` evaluates a checkpoint's stop query: the
# goal graph plus one sj:Receipt node per ALIVE gate, serialized as N-Triples
# and queried with the oxigraph NIF (GgenIgniter.Native.GraphNif.query_turtle),
# the ASK rewritten to its existence-equivalent `SELECT * ... LIMIT 1`
# (SPARQL 1.1 section 16.3). It is the executable half of the crown equation
# until the CE23 root court (CE23-9) lands; it asserts no receipt anywhere.
#
#   cd <ggen_igniter checkout> && MIX_ENV=test mix run <this file> <goal.ttl> [GATE_ID ...]
#
# Each GATE_ID (dcterms:identifier, e.g. CE23-0) gets a synthetic ALIVE
# receipt node. Prints `STOP=true` or `STOP=false`; exits 0 either way (the
# answer is the output), 1 when the query cannot be evaluated.
[goal | alive] = System.argv()
sj = "https://ggen-igniter.dev/ontology/semantic-jira#"
dct = "http://purl.org/dc/terms/"
root = RDF.iri("https://ggen-igniter.dev/sjira/chatman-26.9.23#GC-CE-26.9.23")
graph = RDF.Turtle.read_file!(goal)

[query] =
  graph
  |> RDF.Graph.get(root)
  |> RDF.Description.get(RDF.iri(sj <> "stopQuery"))
  |> Enum.map(&RDF.Literal.value/1)

projected =
  Enum.reduce(RDF.Graph.descriptions(graph), graph, fn description, acc ->
    ids =
      description
      |> RDF.Description.get(RDF.iri(dct <> "identifier"), [])
      |> Enum.map(&RDF.Literal.value/1)

    case ids do
      [id] ->
        if id in alive do
          receipt = RDF.iri("urn:ce23:stop-witness:receipt:" <> id)

          acc
          |> RDF.Graph.add({description.subject, RDF.iri(sj <> "receipt"), receipt})
          |> RDF.Graph.add({receipt, RDF.type(), RDF.iri(sj <> "Receipt")})
          |> RDF.Graph.add({receipt, RDF.iri(sj <> "standing"), RDF.literal("ALIVE")})
        else
          acc
        end

      _ ->
        acc
    end
  end)

ask = ~r/\A((?:\s*(?:#[^\n]*(?:\n|\z)|(?:PREFIX|BASE)\b[^\n]*(?:\n|\z)))*\s*)ASK\b/i
select = Regex.replace(ask, query, "\\1SELECT *", global: false) <> "\nLIMIT 1\n"

case GgenIgniter.Native.GraphNif.query_turtle(RDF.NTriples.write_string!(projected), select) do
  {:ok, rows} ->
    IO.puts("STOP=#{rows != []} (ALIVE gates: #{length(alive)})")

  {:error, reason} ->
    IO.puts("STOP query failed: #{inspect(reason)}")
    System.halt(1)
end
