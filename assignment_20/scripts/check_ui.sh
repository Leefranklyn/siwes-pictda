#!/usr/bin/env bash
export LC_ALL=C.UTF-8
paths="templates students/templates core/templates accounts/templates theme/static_src/src students/templatetags students/forms.py"
fail=0
check() {
  out=$(grep -rnE --include='*.html' --include='*.css' --include='*.js' --include='*.py' "$1" $paths 2>/dev/null)
  if [ -n "$out" ]; then echo "$out"; echo "FOUND: $2"; fail=1; fi
}
checkp() {
  out=$(grep -rnP --include='*.html' --include='*.css' --include='*.js' --include='*.py' "$1" $paths 2>/dev/null)
  if [ -n "$out" ]; then echo "$out"; echo "FOUND: $2"; fail=1; fi
}
check 'gradient|bg-linear|bg-radial|bg-conic' 'gradients are banned'
check 'backdrop-blur|backdrop-filter|blur-' 'blur and glass effects are banned'
check 'shadow-(sm|md|lg|xl|2xl)|drop-shadow' 'shadows are banned'
check 'uppercase|tracking-(wide|wider|widest)' 'uppercase and tracked text are banned'
check 'animate-(pulse|bounce|ping|spin)' 'decorative animation is banned'
check 'hover:(scale-|-translate|translate-y)' 'hover lift and scale are banned'
check '(bg|text|border|ring|from|to|via|fill|stroke|divide)-(gray|slate|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-[0-9]' 'default Tailwind colors are banned'
check 'seamless|effortless|powerful|streamline|empower|unlock|revolutioni|all-in-one|next-generation' 'hype words are banned'
checkp '[\x{1F000}-\x{1FFFF}\x{2600}-\x{27BF}\x{2190}-\x{21FF}\x{2B00}-\x{2BFF}\x{FE0F}]' 'emoji and symbol characters are banned'
checkp '[\x{00B7}\x{2014}\x{2013}]' 'middle dots and long dashes are banned in UI text'
if [ $fail -eq 0 ]; then echo "UI check passed"; else exit 1; fi
