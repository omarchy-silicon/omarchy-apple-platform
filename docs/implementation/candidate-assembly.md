# F-05 candidate assembly

Candidate assembly accepts only the closed candidate-assembly input schema and emits a canonical structural manifest after every injected authority and content-addressed-store check succeeds. The command is read-only and structural verification remains `STRUCTURAL_ONLY`; promotion and release authorization remain outside this slice.

The JSON Schema closes representable shape constraints, including bounded identifiers and strings, exact source commit shape, nonempty unique collections, and the nine required gate positions. Lexicographic ordering of identifiers and digest collections is a semantic constraint that Draft 2020-12 cannot express portably here; the generated consumer model enforces those collections as sorted and unique before any authority or CAS call.
