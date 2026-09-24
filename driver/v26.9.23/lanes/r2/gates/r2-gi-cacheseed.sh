#!/bin/sh
# R2-GI-CACHESEED gate (static, on .github/workflows/ci.yml): the deps and NIF cargo-target
# caches are restored with actions/cache/restore and saved with actions/cache/save by
# explicit steps placed BEFORE "mix test" (so a red/timed-out suite still seeds them),
# with the restore step's primary key and a byte-identical path; _build is NOT saved early.
# usage: r2-gi-cacheseed.sh [subject-worktree]
set -eu
cd "${1:-$PWD}"
ruby -ryaml -e '
st = YAML.load_file(".github/workflows/ci.yml")["jobs"]["test"]["steps"]
ti = st.index { |x| x["name"] == "mix test" } or abort("no mix test step")
ok = true
{ "deps" => "deps\n~/.hex\n~/.mix\n", "nif" => "native/ggen_graph_nif/target" }.each do |tag, path|
  r = st.index { |x| x["uses"].to_s.start_with?("actions/cache/restore@") && x.dig("with", "path") == path }
  s = st.index { |x| x["uses"].to_s.start_with?("actions/cache/save@") && x.dig("with", "path") == path }
  good = r && s && r < s && s < ti && st[s].dig("with", "key").to_s.include?("steps.#{st[r]["id"]}.outputs.cache-primary-key")
  puts "#{tag}: restore=#{r.inspect} save=#{s.inspect} mix_test=#{ti} #{good ? "OK" : "FAIL"}"
  ok &&= good
end
early_build = st[0...ti].any? { |x| x["uses"].to_s.start_with?("actions/cache/save@") && x.dig("with", "path") == "_build" }
puts "_build saved before tests: #{early_build}"
exit(ok && !early_build ? 0 : 1)'
