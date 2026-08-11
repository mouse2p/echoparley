# Generated API reference

## `echoparley.adapters`

- `AdapterAction` (class): AdapterAction(tokens: 'tuple[str, ...]', delay_ms: 'int' = 0, finished: 'bool' = True)
- `DialogueAdapter` (class): Base class for protocol classes.
- `LoopbackHTTPAdapter` (class): HTTP adapter restricted to an explicit local mock endpoint.
- `ReplayAdapter` (class): Replay validated action mappings without generating new content.
- `ScriptedAdapter` (class): Return declared actions in order for deterministic offline tests.
- `adapter_capabilities` (function): Expose stable capability metadata without invoking the adapter.

## `echoparley.apidoc`

- `APIEntry` (class): One public module-local function or class and its docstring summary.
- `api_inventory_mapping` (function): Return exhaustive JSON-compatible API entries under schema 1.0.
- `missing_docstrings` (function): Return public names that lack a usable docstring summary.
- `public_api_entries` (function): Inspect public functions and classes defined by one package module.
- `render_api_entry` (function): Render one API entry as a compact Markdown definition item.
- `render_api_reference` (function): Render a complete Markdown reference for distinct module names.
- `render_module_reference` (function): Render all public module-local APIs from live docstrings.

## `echoparley.artifacts`

- `ArtifactEnvelope` (class): A versioned payload with a checksum covering its semantic identity.
- `bytes_checksum` (function): Return a SHA-256 checksum for an exact byte representation.
- `canonical_json` (function): Encode JSON with stable ordering and no non-standard numeric values.
- `content_checksum` (function): Return a SHA-256 checksum over canonical UTF-8 JSON.
- `decode_jsonl` (function): Decode and verify canonical JSONL bytes.
- `encode_jsonl` (function): Encode envelopes as newline-terminated canonical JSONL.

## `echoparley.audio`

- `AudioBuffer` (class): Finite mono samples normalized to the closed interval [-1, 1].
- `FrameSpan` (class): Half-open sample interval represented by one analysis frame.
- `decode_pcm16` (function): Decode little-endian signed PCM16 into normalized float samples.
- `encode_pcm16` (function): Encode normalized mono samples, optionally clipping out-of-range values.
- `frame_audio` (function): Return copied frames, optionally zero-padding the final partial frame.
- `frame_spans` (function): Describe exact source coverage for every frame returned by ``frame_audio``.
- `read_wav` (function): Read mono PCM16 WAV bytes under the package audio convention.
- `write_wav` (function): Serialize a mono buffer to a standards-compatible PCM16 WAV.

## `echoparley.bench`

- `BaselineComparison` (class): BaselineComparison(case: 'str', ratio: 'float', within_tolerance: 'bool')
- `BenchmarkBaseline` (class): BenchmarkBaseline(case: 'str', mean_ms: 'float', tolerance_ratio: 'float' = 10.0)
- `BenchmarkEnvironment` (class): BenchmarkEnvironment(python: 'str', numpy: 'str', platform: 'str', package: 'str')
- `BenchmarkSample` (class): BenchmarkSample(case: 'str', repeat: 'int', elapsed_ms: 'float', work_seconds: 'float | None' = None)
- `BenchmarkSummary` (class): BenchmarkSummary(case: 'str', repeats: 'int', mean_ms: 'float', median_ms: 'float', p95_ms: 'float', stdev_ms: 'float')
- `RegressionGuard` (class): RegressionGuard(case: 'str', upper_bound_ms: 'float')
- `ThroughputSummary` (class): ThroughputSummary(case: 'str', work_items: 'int', items_per_second: 'float')
- `benchmark_environment` (function): Capture versions needed to interpret machine-dependent measurements.
- `benchmark_result_record` (function): Assemble metadata and computed summaries for a benchmark suite.
- `benchmark_run_metadata` (function): Describe reproducibility inputs without treating timings as portable.
- `benchmark_simulator` (function): Measure deterministic synthetic dialogue simulation throughput.
- `benchmark_streams` (function): Measure mapping roundtrips over generated deterministic streams.
- `benchmark_suite` (function): Run all offline cases with shared seed and repeat settings.
- `benchmark_summaries` (function): Group suite samples by case in stable first-seen order.
- `benchmark_throughput` (function): Convert measured mean latency to item throughput.
- `benchmark_units` (function): Measure fitting and extraction over a small seeded synthetic matrix.
- `compare_benchmark_baseline` (function): Compare means by ratio so only order-of-magnitude drift fails.
- `decode_benchmark_jsonl` (function): Decode verified benchmark-sample envelopes from canonical JSONL.
- `decode_benchmark_summaries` (function): Decode verified benchmark-summary envelopes from canonical JSONL.
- `encode_benchmark_jsonl` (function): Encode samples in the common checksummed artifact envelope.
- `encode_benchmark_summaries` (function): Encode checksummed summary artifacts distinct from raw samples.
- `merge_benchmark_runs` (function): Merge runs and resequence repeats independently for each case.
- `run_benchmark` (function): Warm an operation, then measure repeats using an injectable clock.
- `select_benchmark_case` (function): Select one nonempty case from a combined benchmark run.
- `summarize_samples` (function): Summarize samples for one case with production-point rounding.

## `echoparley.cascade`

- `AlignedTTSUnit` (class): AlignedTTSUnit(identifier: 'int', start_ms: 'int', end_ms: 'int', text: 'str')
- `CascadeAdapter` (class): CascadeAdapter(cascade: 'ScriptedCascade', latest_label: 'str' = 'silence')
- `CascadeConfiguration` (class): CascadeConfiguration(enabled_stages: 'tuple[str, ...]' = ('vad', 'stt', 'punctuation', 'lm', 'tts'), delays_ms: 'tuple[int, ...]' = (10, 80, 15, 60, 90))
- `CascadeDegradation` (class): CascadeDegradation(failed_stage: 'str', fallback: 'str', retained_output: 'str')
- `CascadeExecution` (class): Outputs, timing, and optional failure from one local mock cascade.
- `CascadeResult` (class): CascadeResult(transcript: 'str', response: 'str', units: 'tuple[int, ...]', stage_delays_ms: 'tuple[int, int, int]')
- `MockPunctuation` (class): Deterministic transcript casing and terminal punctuation stage.
- `MockTTSAlignment` (class): MockTTSAlignment(unit_ms: 'int' = 40)
- `MockVAD` (class): Energy threshold stage for offline synthetic fixtures.
- `ScriptedCascade` (class): ScriptedCascade(stt: 'TextStage', text_lm: 'TextStage', tts: 'TextStage', stage_delays_ms: 'tuple[int, int, int]' = (80, 60, 90))
- `SeededFaultPlan` (class): SeededFaultPlan(seed: 'int', failure_rate: 'float', stages: 'tuple[str, ...]' = ('vad', 'stt', 'punctuation', 'lm', 'tts'))
- `StageLatencyLedger` (class): StageLatencyLedger(timings: 'tuple[StageTiming, ...]' = ())
- `StageObservation` (class): Compact observable input/output labels for one mock pipeline stage.
- `StageTiming` (class): StageTiming(name: 'str', delay_ms: 'int')
- `TextStage` (class): Base class for protocol classes.
- `VoiceActivitySpan` (class): VoiceActivitySpan(start_frame: 'int', end_frame: 'int')
- `cascade_execution_mapping` (function): Serialize observable cascade results without raw synthetic audio.
- `compare_cascade_executions` (function): Compare stage delays and output sizes from two synthetic executions.
- `compare_paths` (function): Compare measured synthetic path latency and unit counts.
- `degrade_after_failure` (function): Choose an explicit local fallback without pretending the stage succeeded.
- `execute_mock_cascade` (function): Run configured local mock stages and retain observable intermediate labels.
- `stage_latency_mapping` (function): Return per-stage measured mock delays while rejecting duplicates.
- `transform_cascade_text` (function): Apply the text-only portion of one named mock cascade stage.

## `echoparley.cli`

- `build_parser` (function): Build the complete offline CLI parser shared with completion generation.
- `main` (function): Run the command-line interface and return a process status.

## `echoparley.completion`

- `bash_completion` (function): Generate a dependency-free Bash completion function.
- `command_names` (function): Return sorted subcommand names declared by a parser.
- `command_options` (function): Return sorted long options for each subcommand.
- `completion_assets` (function): Return stable relative filenames and generated contents.
- `zsh_completion` (function): Generate a compact Zsh command completion definition.

## `echoparley.config`

- `ExperimentConfig` (class): Core reproducibility and audio conventions for a run.

## `echoparley.context`

- `ContextBenchmarkConfig` (class): ContextBenchmarkConfig(token_budget: 'int', relevant_topics: 'frozenset[str]')
- `ContextWindow` (class): ContextWindow(turns: 'tuple[ConversationTurn, ...]', used_tokens: 'int', evicted_turns: 'int')
- `EvictionPolicy` (class): Stable names for deterministic context-selection strategies.
- `RetentionScore` (class): RetentionScore(policy: 'EvictionPolicy', retained_relevant: 'int', total_relevant: 'int', used_tokens: 'int')
- `benchmark_context_policies` (function): Measure relevant-turn retention for all policies on the same history.
- `best_retention_policy` (function): Choose highest recall, then lowest token use, then stable policy name.
- `context_benchmark_report` (function): Serialize measured policy retention with stable policy ordering.
- `context_retention_score` (function): Score retained planted topics for policy comparisons.
- `parse_eviction_policy` (function): Parse a policy name with an actionable error for configuration surfaces.
- `planted_topic_salience` (function): Assign transparent salience using planted topic membership and recency.
- `select_context` (function): Keep the newest complete turns that fit a non-negative budget.
- `select_context_by_policy` (function): Select context through a stable policy interface.
- `select_context_with_reserve` (function): Select history after reserving capacity for a future response.
- `select_salient_context` (function): Select high-scoring whole turns, breaking ties toward recent turns.
- `select_turn_boundary_context` (function): Keep newest complete contiguous topic segments without splitting one.

## `echoparley.duplex`

- `BargeInMode` (class): Enum where members are also (and must be) strings
- `BargeInStrategy` (class): BargeInStrategy(mode: 'BargeInMode' = <BargeInMode.IMMEDIATE_YIELD: 'immediate-yield'>, grace_ms: 'int' = 120, competitive_threshold: 'float' = 0.9)
- `DuplexEngine` (class): Deterministic state machine with explicit partial-generation state.
- `DuplexState` (class): Enum where members are also (and must be) strings
- `InterruptionDecision` (class): InterruptionDecision(should_yield: 'bool', reason: 'str')
- `Transition` (class): Transition(previous: 'DuplexState', current: 'DuplexState', event: 'EventKind', time_ms: 'int', reason: 'str')
- `TurnPolicy` (class): TurnPolicy(patience_ms: 'int' = 200, hangover_ms: 'int' = 120, min_turn_ms: 'int' = 100, max_turn_ms: 'int' = 10000, interrupt_threshold: 'float' = 0.75)
- `decide_interruption` (function): Apply one deterministic barge-in strategy to a remote speech claim.

## `echoparley.events`

- `EndpointEvent` (class): EndpointEvent(kind: 'EventKind', time_ms: 'int', posterior: 'float' = 1.0, speaker: 'str' = 'remote')
- `EventKind` (class): Enum where members are also (and must be) strings

## `echoparley.features`

- `analysis_window` (function): Return a periodic Hann, Hamming, or rectangular window.
- `hertz_to_mel` (function): Map non-negative Hertz values to the HTK mel convention.
- `log_mel_features` (function): Project power spectra onto mel bands and apply a natural-log floor.
- `mel_filterbank` (function): Build area-normalized triangular filters across the usable spectrum.
- `mel_to_hertz` (function): Invert the HTK mel transform for non-negative values.
- `power_spectrum` (function): Compute squared-magnitude real FFT spectra for a frame matrix.
- `sliding_statistics` (function): Concatenate local mean and standard deviation with clipped boundaries.
- `temporal_deltas` (function): Compute centered deltas with replicated edge frames.

## `echoparley.latency`

- `LatencyBudget` (class): LatencyBudget(decision_ms: 'int', first_unit_ms: 'int')
- `TurnLatency` (class): TurnLatency(perception_ms: 'int', decision_ms: 'int', first_unit_ms: 'int')
- `latency_summary` (function): Return rounded min, median, p95, and maximum first-unit delays.

## `echoparley.memory`

- `dump_memory` (function): Encode one conversation state in a checksummed JSONL envelope.
- `load_memory` (function): Decode exactly one verified conversation-memory envelope.

## `echoparley.metrics`

- `BoundaryConfusion` (class): BoundaryConfusion(true_positive: 'int', false_positive: 'int', false_negative: 'int')
- `BoundaryScores` (class): BoundaryScores(precision: 'float', recall: 'float', f1: 'float', matches: 'int')
- `ConfidenceInterval` (class): ConfidenceInterval(estimate: 'float', lower: 'float', upper: 'float', confidence: 'float')
- `FloorControl` (class): FloorControl(speaker_ms: 'dict[str, int]', overlap_ms: 'int', silence_ms: 'int')
- `FloorDominance` (class): FloorDominance(dominant_speaker: 'str | None', dominant_share: 'float', overlap_share: 'float', silence_share: 'float')
- `LatencyDistribution` (class): LatencyDistribution(count: 'int', minimum_ms: 'int', mean_ms: 'float', stdev_ms: 'float', maximum_ms: 'int', percentiles: 'LatencyPercentiles')
- `LatencyPercentiles` (class): LatencyPercentiles(p50_ms: 'float', p90_ms: 'float', p99_ms: 'float')
- `accuracy` (function): Return bounded floor-hold accuracy with an empty-set identity.
- `bootstrap_mean_interval` (function): Estimate a deterministic percentile bootstrap interval for a sample mean.
- `bootstrap_median_interval` (function): Estimate a deterministic percentile bootstrap interval for the median.
- `boundary_confusion` (function): Return one-to-one greedy boundary match counts.
- `boundary_decisions` (function): Project boundary timestamps onto fixed half-open agreement bins.
- `chance_corrected_agreement` (function): Compute Cohen-style kappa for two aligned boundary decision vectors.
- `error_rate` (function): Return a bounded false-interrupt or missed-barge-in rate.
- `evaluation_table` (function): Assemble bounded turn metrics with an explicit synthetic provenance label.
- `expanded_evaluation_record` (function): Assemble measured synthetic turn-taking metrics under schema 1.0.
- `floor_control_statistics` (function): Measure planted speaker occupancy, overlap, and silence on a millisecond grid.
- `floor_dominance` (function): Summarize occupancy shares over a measured dialogue duration.
- `latency_cdf` (function): Return unique latency thresholds and cumulative observed fractions.
- `latency_distribution` (function): Summarize non-negative response latencies with population deviation.
- `latency_percentiles` (function): Return linear-interpolated latency percentiles rounded at production.
- `match_boundaries` (function): Greedily match each prediction to one planted boundary within tolerance.
- `normalized_transition_entropy` (function): Scale observed transition entropy by the maximum for observed pairs.
- `transition_entropy` (function): Measure entropy of observed speaker-to-speaker transition pairs in bits.
- `transition_matrix` (function): Count ordered speaker transitions with stable row and column keys.

## `echoparley.proptest`

- `CaseSet` (class): Generated values together with the seed needed to reproduce them.
- `PropertyFailure` (class): PropertyFailure(seed: 'int', case_index: 'int', original: 'T', minimal: 'T')
- `PropertyRun` (class): Summary of evaluated cases plus an optional minimized failure.
- `check_cases` (function): Return the first failing case and greedily minimized reproduction.
- `context_budget_invariant` (function): Check reported cost equals retained turns and never exceeds the cap.
- `evaluate_property` (function): Evaluate a named property and report how many cases reached the failure.
- `generate_endpoint_traces` (function): Generate chronological endpoint evidence for state-machine properties.
- `generate_sessions` (function): Generate contiguous, monotone session traces for replay properties.
- `generate_streams` (function): Generate valid time-aligned streams with mixed token namespaces.
- `generate_turns` (function): Generate histories with planted topics and exact token costs.
- `legal_duplex_invariant` (function): Check that SPEAK is entered only from TAKE_FLOOR for an event trace.
- `property_suite_report` (function): Combine distinct executable property runs into a stable report.
- `run_context_suite` (function): Evaluate exact token accounting over generated histories and budgets.
- `run_duplex_suite` (function): Evaluate legal state entry across generated endpoint traces.
- `run_session_suite` (function): Evaluate byte-identical replay across generated event sessions.
- `run_stream_suite` (function): Evaluate exact mapping roundtrip across generated unified streams.
- `session_roundtrip_invariant` (function): Check byte-stable encode/decode reconstruction for generated sessions.
- `shrink_endpoint_trace` (function): Remove event chunks while preserving each retained event timestamp.
- `shrink_non_negative` (function): Return deterministic candidates approaching the minimal value zero.
- `shrink_sequence` (function): Generate ordered chunk removals, from coarse halves to single items.
- `shrink_session` (function): Remove chunks and renumber retained events for valid replay artifacts.
- `shrink_stream` (function): Shrink token content while retaining policy and schema metadata.
- `stream_roundtrip_invariant` (function): Check exact public mapping roundtrip for a generated stream.

## `echoparley.prosody`

- `PitchSummary` (class): PitchSummary(voiced_frames: 'int', voiced_fraction: 'float', minimum_hz: 'float', median_hz: 'float', maximum_hz: 'float')
- `PitchTrack` (class): Frame-center times, F0 estimates, and normalized voicing strengths.
- `ProsodicFeatures` (class): Transparent measurements derived from synthetic timing and pitch.
- `ToneEvent` (class): A local synthetic pitch movement at a frame time.
- `ToneScenario` (class): ToneScenario(samples: 'FloatArray', sample_rate: 'int', frequencies_hz: 'tuple[float, ...]', boundaries: 'tuple[int, ...]')
- `annotate_tone_events` (function): Label adjacent voiced rises and falls in a synthetic pitch track.
- `autocorrelation_f0` (function): Estimate frame-level F0 without external models or downloaded weights.
- `median_contour` (function): Suppress isolated voiced pitch outliers using an odd-width median.
- `moving_average_contour` (function): Smooth voiced F0 values while leaving unvoiced frames at zero.
- `prosodic_features` (function): Combine timing, pause, and voiced-pitch measurements into one vector.
- `prosody_array` (function): Return the documented five-value feature order for clustering.
- `smooth_pitch_track` (function): Apply median suppression followed by spline-free moving averaging.
- `summarize_pitch` (function): Summarize voiced F0 frames with explicit empty-track identities.
- `synthesize_tone_scenario` (function): Create contiguous pure-tone segments with planted sample boundaries.
- `voiced_segments` (function): Return half-open frame spans for contiguous positive-F0 regions.

## `echoparley.reports`

- `event_diff_rows` (function): Render insert/delete/change rows with semantic CSS classes.
- `event_diff_svg` (function): Render semantic event differences in a deterministic standalone SVG.
- `latency_histogram` (function): Count non-negative delays into deterministic fixed-width bins.
- `normalize_svg` (function): Remove explicitly volatile generation attributes before golden comparison.
- `session_comparison_metadata` (function): Describe exact inputs to a deterministic session comparison.
- `session_diff_report_svg` (function): Combine paired timelines and semantic diff rows in one SVG.
- `session_timeline_group` (function): Render one session as a labeled SVG group for composition.
- `side_by_side_session_svg` (function): Compose two replay timelines using independent time scales.
- `strategy_comparison_svg` (function): Render measured synthetic strategy yield rates as deterministic bars.
- `svg_document` (function): Wrap trusted SVG fragments with validated positive dimensions.
- `svg_report` (function): Render a timeline and metric table with stable ordering.

## `echoparley.runtime`

- `CancellationToken` (class): CancellationToken(cancelled: 'bool' = False, reason: 'str | None' = None)
- `TickConfig` (class): TickConfig(interval_ms: 'int' = 20, accelerated: 'bool' = True)
- `record_ticks` (function): Run accelerated ticks into a closed session event tuple.
- `run_ticks` (function): Run ticks and return executed logical times, retaining partial progress.

## `echoparley.scenarios`

- `BackchannelKind` (class): Planted listener-response functions, not inferred pragmatics.
- `CorpusStatistics` (class): CorpusStatistics(dialogues: 'int', turns: 'int', speakers: 'int', overlaps: 'int', backchannels: 'int', duration_ms: 'int')
- `FloorContentionPolicy` (class): Deterministic planted rules for choosing among simultaneous claimants.
- `NoisyChannelScenario` (class): NoisyChannelScenario(dialogue: 'DialogueScenario', mishearings: 'tuple[PlantedMishearing, ...]')
- `PlantedMishearing` (class): Known substitution attached to a synthetic noisy-channel turn.
- `ScenarioAnnotations` (class): Supplemental planted labels keyed by dialogue turn index.
- `casual_backchannel_annotations` (function): Derive labels only for explicitly planted backchannel turns.
- `casual_backchannel_scenario` (function): Build a long casual turn with all planted backchannel functions.
- `classify_planted_backchannel` (function): Look up a deliberately scripted backchannel label.
- `corpus_report` (function): Build a checksummed report whose measurements are synthetic counts.
- `corpus_statistics` (function): Aggregate transparent counts over a synthetic scenario collection.
- `decode_scenario_corpus` (function): Decode schema-2 scenario artifacts and restore their typed annotations.
- `encode_scenario_corpus` (function): Encode a nonempty ordered corpus of planted scenario manifests.
- `long_topic_scenario` (function): Generate a long two-speaker history with sparse planted target-topic turns.
- `make_expanded_scenario` (function): Resolve an expanded planted scenario by its stable catalog name.
- `migrate_scenario_manifest` (function): Upgrade a trusted schema-1 manifest to schema 2 without changing turns.
- `negotiation_scenario` (function): Build a negotiation with a deliberately contested floor interval.
- `noisy_channel_scenario` (function): Build a repair exchange with an explicit planted transcription error.
- `resolve_floor_contention` (function): Choose a speaker from `(name, waiting_ms)` claims with stable ties.
- `scenario_catalog` (function): Return all expanded Phase 2 scenarios at one reproducible seed.
- `scenario_from_manifest` (function): Restore and validate a dialogue plus supplemental labels from schema 2.
- `scenario_manifest` (function): Encode complete planted dialogue ground truth using manifest schema 2.0.
- `scenario_manifest_envelope` (function): Wrap schema-2 planted ground truth in a checksummed artifact envelope.
- `scenario_topics` (function): Return planted topics in temporal order, optionally collapsing repeats.
- `three_speaker_scenario` (function): Build a three-party exchange with a planted simultaneous floor claim.
- `topic_drift_scenario` (function): Build a dialogue whose planted topic changes twice.
- `tutorial_scenario` (function): Build a tutorial exchange with a planted clarification and answer.
- `validate_scenario_annotations` (function): Reject supplemental labels that do not point at matching planted turns.

## `echoparley.schema`

- `SchemaRegistry` (class): Track supported versions per artifact kind without global state.
- `SchemaVersion` (class): A small, strictly positive major/minor schema identifier.
- `migrate_mapping` (function): Apply registered same-major minor migrations in order.

## `echoparley.session`

- `DifferenceKind` (class): Enum where members are also (and must be) strings
- `DifferenceSummary` (class): DifferenceSummary(inserted: 'int', deleted: 'int', changed: 'int')
- `SessionDifference` (class): SessionDifference(sequence: 'int', left: 'SessionEvent | None', right: 'SessionEvent | None')
- `SessionEvent` (class): SessionEvent(sequence: 'int', time_ms: 'int', kind: 'str', payload: 'dict[str, Any]')
- `SessionRecorder` (class): Assign monotonic sequences while retaining clean partial sessions.
- `SessionReplayer` (class): SessionReplayer(events: 'tuple[SessionEvent, ...]', cursor: 'int' = 0)
- `decode_session` (function): Decode verified session events and enforce contiguous sequences.
- `diff_sessions` (function): Return event-exact differences including missing tails.
- `difference_kind` (function): Classify a left-to-right event difference.
- `encode_session` (function): Encode contiguous session events as canonical checksummed JSONL.
- `session_digest` (function): Hash the exact canonical replay bytes.
- `summarize_differences` (function): Count insert, delete, and change operations in a replay diff.

## `echoparley.simulator`

- `SimulationResult` (class): SimulationResult(trace: 'tuple[TraceEvent, ...]', latencies: 'tuple[TurnLatency, ...]', planted_boundaries_ms: 'tuple[int, ...]')
- `StrategySweepPoint` (class): StrategySweepPoint(mode: 'BargeInMode', parameter: 'float', yielded: 'bool', decision_reason: 'str')
- `TraceEvent` (class): TraceEvent(time_ms: 'int', agent: 'str', state: 'DuplexState', source: 'str')
- `boundary_agreement` (function): Measure response transitions near planted turn endpoints.
- `planted_events` (function): Convert annotations into stable start/end events, preserving overlaps.
- `simulate_dialogue` (function): Replay planted endpoints into two deterministic turn engines.
- `simulation_metadata` (function): Describe a synthetic run without implying model-quality evaluation.
- `strategy_comparison_table` (function): Aggregate yielded proportions for a synthetic parameter sweep.
- `sweep_barge_in_strategies` (function): Evaluate strategy decisions on identical planted interruption evidence.

## `echoparley.snippets`

- `PythonSnippet` (class): Runnable source plus its one-based Markdown starting line.
- `execute_snippets` (function): Compile and execute each trusted project-documentation snippet independently.
- `extract_python_snippets` (function): Extract fenced blocks labeled `python echoparley-run`.

## `echoparley.state`

- `ConversationState` (class): ConversationState(turns: 'tuple[ConversationTurn, ...]' = (), topic_stack: 'tuple[str, ...]' = (), pending_acts: 'tuple[str, ...]' = ())
- `ConversationTurn` (class): ConversationTurn(speaker: 'str', text: 'str', token_count: 'int', start_ms: 'int', end_ms: 'int', topic: 'str | None' = None)

## `echoparley.stream`

- `StreamToken` (class): StreamToken(kind: 'TokenKind', value: 'str', speaker: 'str', start_ms: 'int', end_ms: 'int')
- `TokenKind` (class): Enum where members are also (and must be) strings
- `UnifiedStream` (class): UnifiedStream(tokens: 'tuple[StreamToken, ...]', policy: 'str', schema_version: 'str' = '1.0')
- `bound_turn` (function): Wrap content with zero-duration start and end controls.
- `dense_interleave` (function): Emit a text token after each fixed number of units, then drain either side.
- `split_stream` (function): Recover each namespace without changing its within-kind order.
- `stream_from_mapping` (function): Restore a stream from a trusted JSON-compatible mapping.
- `stream_to_mapping` (function): Convert a unified stream to its complete schema mapping.
- `strict_turn_interleave` (function): Order whole turns by their first timestamp without mixing content.
- `time_aligned_interleave` (function): Sort individual tokens using deterministic timestamp and namespace ties.
- `validate_token_namespace` (function): Ensure textual spellings agree with the declared token kind.

## `echoparley.synth`

- `DialogueScenario` (class): A reproducible script for up to three speakers with planted ground truth.
- `SpeakerProfile` (class): Parameters for a synthetic harmonic signal, not a voice identity.
- `TurnAnnotation` (class): Ground-truth interval deliberately planted by a scenario template.
- `backchannel_scenario` (function): Create short listener acknowledgements inside a long planted turn.
- `barge_in_scenario` (function): Create a deliberate interruption while the other speaker holds the floor.
- `booking_scenario` (function): Create a short synthetic booking exchange with a floor-holding pause.
- `make_scenario` (function): Resolve a built-in scenario by its stable public name.
- `question_scenario` (function): Create a synthetic question-and-answer structure with planted topics.
- `render_dialogue` (function): Render each speaker on an independent channel using planted intervals.
- `synthesize_formants` (function): Generate a seeded harmonic-plus-formant fixture with gentle envelopes.

## `echoparley.text`

- `BPEModel` (class): An ordered tuple of adjacent-symbol merges.
- `Vocabulary` (class): Stable token-to-ID mapping with protected turn and unknown symbols.
- `bpe_from_mapping` (function): Restore a schema-1.0 BPE model and reject drift.
- `bpe_to_mapping` (function): Serialize a BPE model under schema version 1.0.
- `build_vocabulary` (function): Build deterministic reserved, text, then speech-unit namespaces.
- `decode_subwords` (function): Decode tokens, rejecting streams without complete word markers.
- `encode_subwords` (function): Encode normalized words while keeping an explicit word boundary.
- `normalize_text` (function): Apply NFKC, optional case folding, and canonical whitespace.
- `train_bpe` (function): Train merges by frequency with lexical tie breaking.

## `echoparley.topics`

- `TopicScores` (class): TopicScores(precision: 'float', recall: 'float')
- `TopicTracker` (class): TopicTracker(lexicon: 'dict[str, frozenset[str]]')
- `topic_scores` (function): Score topic labels with defined empty-set behavior.

## `echoparley.torch_models`

- `TrainingSummary` (class): TrainingSummary(initial_loss: 'float', final_loss: 'float', steps: 'int', data_origin: 'str' = 'deterministic-synthetic')
- `constrained_sample` (function): Choose the greatest allowed scaled logit with deterministic tie breaking.
- `torch_available` (function): Report whether the optional CPU-oriented PyTorch extra can be imported.
- `train_lm_demo` (function): Train a small causal next-token table on a planted repeating stream.
- `train_vq_demo` (function): Fit a tiny VQ-like bottleneck to synthetic formant-feature clusters.

## `echoparley.units`

- `CodebookUsage` (class): Observed occupancy and entropy perplexity for a fixed codebook.
- `KMeansCodebook` (class): Centroids ordered by their seeded initialization slots.
- `PCAProjection` (class): Mean-centered orthonormal projection fitted with deterministic SVD.
- `UnitExtractor` (class): Composed PCA projection and semantic codebook.
- `UnitSpan` (class): A semantic unit aligned to a half-open frame interval.
- `align_unit_runs` (function): Map collapsed units to contiguous frame spans.
- `codebook_usage` (function): Measure unit usage without claiming semantic quality.
- `collapse_units` (function): Run-length encode unit IDs into IDs and positive frame durations.
- `expand_units` (function): Expand run-length encoded units to one ID per frame.
- `fit_kmeans` (function): Fit Lloyd k-means from distinct seeded observations.
- `fit_pca` (function): Fit a projection while fixing component signs for stable serialization.
- `fit_prosody_unit_extractor` (function): Fit units over acoustic columns augmented by measured prosodic columns.
- `fit_unit_extractor` (function): Fit both deterministic stages on the same synthetic feature matrix.
- `retained_variance` (function): Return the finite-sample variance fraction represented by a projection.

## `echoparley.vq`

- `CodebookHealth` (class): CodebookHealth(size: 'int', occupied: 'int', occupancy_ratio: 'float', perplexity: 'float', effective_size: 'float')
- `CollapseAssessment` (class): CollapseAssessment(collapsed: 'bool', occupancy_below_threshold: 'bool', perplexity_below_threshold: 'bool')
- `EMACodebook` (class): EMACodebook(centroids: 'FloatArray', counts: 'FloatArray', sums: 'FloatArray')
- `VQLossCurve` (class): VQLossCurve(reconstruction: 'tuple[float, ...]', quantization: 'tuple[float, ...]')
- `assess_collapse` (function): Apply explicit experiment thresholds to codebook diagnostics.
- `codebook_health` (function): Measure occupancy and entropy without implying representation quality.
- `dead_code_indices` (function): Return code indices below an explicit usage-count threshold.
- `ema_codebook_step` (function): Apply one exponential-moving-average codebook update.
- `initialize_ema_codebook` (function): Initialize running statistics from finite two-dimensional centroids.
- `revive_dead_codes` (function): Replace dead centroids with distinct seeded synthetic batch embeddings.
- `train_vq_loss_curve` (function): Train a tiny CPU VQ bottleneck on synthetic clusters and return real losses.
- `vq_curve_summary` (function): Report measured loss changes with an explicit synthetic-data label.
- `vq_loss_svg` (function): Render reconstruction and quantization loss without plotting dependencies.
