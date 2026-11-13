# Procedencia de las skills externas

Estas skills se copiaron tal cual desde sus repositorios oficiales (sin modificaciones) el 2026-11-03.
Para actualizarlas, vuelve a descargar el repositorio y reemplaza la carpeta correspondiente.

| Carpeta | Repositorio | Ruta en el repo | Commit | Licencia |
|---|---|---|---|---|
| `frontend-design/` | https://github.com/anthropics/skills | `skills/frontend-design` | `ca45fc496a3436251f191354091d557da31c15b5` | ver `LICENSE.txt` |
| `impeccable/` | https://github.com/pbakaus/impeccable | `.claude/skills/impeccable` | `9fadc41729c38fd47d7ae622b501558653f9d2e9` | Apache 2.0 |
| `deploy-to-vercel/` | https://github.com/vercel-labs/agent-skills | `skills/deploy-to-vercel` | `1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62` | MIT |
| `vercel-react-best-practices/` | https://github.com/vercel-labs/agent-skills | `skills/react-best-practices` | `1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62` | MIT |
| `vercel-react-native-skills/` | https://github.com/vercel-labs/agent-skills | `skills/react-native-skills` | `1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62` | MIT |

Las skills propias del proyecto (`levantar-proyecto`, `nueva-funcionalidad`, `explicar`, `reportar-error`,
`guardar-partida`, `revision-contenido-mascotas`) se escribieron para PetConnect.

**Nota sobre impeccable:** algunos comandos ejecutan `scripts/impeccable(.cmd)`, que la primera vez descarga
su motor (`impeccable-windows-x64.exe`) desde los *releases* de GitHub de pbakaus/impeccable y lo verifica
contra `scripts/engine-checksums.txt` antes de usarlo. Claude pedirá permiso antes de correrlo.
