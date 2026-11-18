# Paralelismo no WarehouseFlow — lote + Cython (sem JS no núcleo)

**Objetivo:** paralelismo **dentro do app**, com núcleo **compilável (C via Cython)**.  
**JavaScript não calcula nem paraleliza** o lote — só a interface residual dos outros modos.

## O que o professor / slides pedem

| Prioridade | No WarehouseFlow |
|------------|------------------|
| Python / C / C++ no núcleo | Motor + ProcessPool + Cython |
| JS **não** no núcleo computacional | Lote = form HTML → Python/Jinja |
| CUDA / OpenCL | Não usados (liberado) |

## Fluxo do lote (server-side)

```text
Form HTML POST /otimizacao/lote
  → Python (cookie JWT)
  → optimize_routes_batch (ProcessPool)
  → Cython/C se compilado, senão Python
  → HTML Jinja com T(1), T(p), S(p), E(p)
```

- Página: `/otimizacao?mode=batch`
- Submit: `POST /otimizacao/lote` (sem `fetch` / sem Worker JS)
- API JSON (Swagger/testes): `POST /optimization/route/batch` (também Python)

## Métricas

| Símbolo | Campo | Fórmula |
|---------|-------|---------|
| T(1) | `sequential_ms` | wall-clock sequencial |
| T(p) | `parallel_ms` | wall-clock com `p` workers |
| S(p) | `speedup` | T(1) / T(p) |
| E(p) | `efficiency` | S(p) / p |

## Compilar o núcleo C (Cython)

Windows precisa do **Microsoft C++ Build Tools**  
https://visualstudio.microsoft.com/visual-cpp-build-tools/  
(workload: Desktop development with C++)

```powershell
pip install cython
cd backend
python build_optimization_native.py build_ext --inplace

$env:PYTHONPATH = "backend"
python -c "from optimization.native_status import native_compiled; print(native_compiled())"
```

Esperado: `True` → badge **Motor Cython/C** na tela do lote.  
Sem compilador: app funciona em Python (`native_compiled=False`).

## Como demonstrar na banca

1. Login (form/cookie).
2. Otimização → **Lote paralelo**.
3. IDs OUTBOUND + workers 2/4 + repeats ≥ 4 → **Otimizar lote**.
4. Mostrar card T(1)/T(p)/S(p)/E(p) gerado pelo **servidor**.
5. Frase:

> “Paralelismo e métricas rodam só no backend (Python + C via Cython). JavaScript não executa o lote; a tela só exibe o HTML do servidor. CUDA/OpenCL não foram necessários.”

## Testes

```powershell
$env:PYTHONPATH = "backend"
python -m pytest tests/test_parallel_batch.py tests/test_api_optimization_batch.py tests/test_otimizacao_lote_ssr.py -q
```
