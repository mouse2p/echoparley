_echoparley_complete() {
  local current
  current="${COMP_WORDS[COMP_CWORD]}"
  COMPREPLY=( $(compgen -W "bench chat compare completion demo eval prosody replay report scenarios simulate synth train units --against --duration --frequency --help --json --message --model --output --repeats --scenario --seed" -- "$current") )
}
complete -F _echoparley_complete echoparley
