#!/bin/bash
# usage: k.sh METHOD PATH [json]
B=https://eu.api.konghq.com/v2/control-planes/YOUR-CONTROL-PLANE-ID/core-entities
if [ -n "$3" ]; then curl -s -X "$1" -H "Authorization: Bearer $KCONNECT_TOKEN" -H 'content-type: application/json' "$B/$2" -d "$3"; else curl -s -X "$1" -H "Authorization: Bearer $KCONNECT_TOKEN" "$B/$2"; fi; echo
