# Day 02 · 读懂被测服务：路由、错误码、状态

> 60 分钟 = 读 20 · 手工打接口 25 · 画图 10 · 记 5
> 今天的产出是一张图：**请求进来之后，服务里发生了什么、什么被改了**。

## 今天结束时要能做到

1. 说出 4 个端点各自做什么、改不改状态；
2. 说清 3 个错误码分别在什么输入下触发；
3. 解释"为什么报价不查库存、下单才查"。

## 1. 读（20 min）

只读 [`game/server.py`](../../game/server.py) 的 89-129 行（`do_GET` / `do_POST`）。
读的时候把路由抄成一张表：

| 方法 | 路径 | 入参 | 改状态吗 | 失败码 |
| --- | --- | --- | --- | --- |
| GET | `/health` | — | 否 | — |
| GET | `/api/odds` | — | 否 | — |
| GET | `/api/leaderboard?limit=` | limit | 否 | `INVALID_QUERY` |
| POST | `/api/draw` | player, seed, index | **是**（写流水） | `INVALID_PLAYER` / `INVALID_INDEX` / `INVALID_SEED` |
| POST | `/api/reset` | — | **是**（清空） | — |

再看 30-52 行的三个函数：`reset()` / `record()` / `leaderboard()`。
注意 `_LOCK` 的作用：所有写操作串行化，因为 `ThreadingHTTPServer` 会并发处理请求。

## 2. 手工打接口（25 min）

起服务（**新开一个终端**，别关）：

```powershell
python -m game.server --port 8199
```

另开终端，按顺序打 5 个请求：

```powershell
# 1) 健康检查：不碰任何状态
Invoke-RestMethod http://127.0.0.1:8199/health

# 2) 奖池概率：只读
Invoke-RestMethod http://127.0.0.1:8199/api/odds

# 3) 抽一次：注意 seed/index 都给了确定值
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8199/api/draw `
  -ContentType application/json -Body '{"player":"day02","seed":7,"index":0}'

# 4) 排行榜：刚才那次抽奖应该出现了
Invoke-RestMethod "http://127.0.0.1:8199/api/leaderboard?limit=5"

# 5) 非法输入：index 给负数
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8199/api/draw `
  -ContentType application/json -Body '{"player":"day02","index":-1}'
```

第 5 步期望报错 `INVALID_INDEX`。**先看错误响应长什么样**（`code` + `message`），
这是 Day 05 写负向用例的素材。

### 加练（10 min，可选）

- 把 `index` 换成 `-1`、`1.5`、`"3"` 各打一次，记录三种报错；
- 抽一次后调用 `/api/reset`，再查排行榜，确认空。

## 3. 画图（10 min）

在纸上或注释里画这条链路：

```
POST /api/draw
  → 读 JSON（失败 → INVALID_JSON）
  → 校验 player（失败 → INVALID_PLAYER）
  → draw(seed, index)  ← 纯函数，不改状态
  → record(player, prize)  ← 加锁写 DRAW_LOG
  → 返回 {prize, player}
```

关键区分：**`draw` 是纯的（给定输入必得同一输出），`record` 才有副作用**。
这就是为什么 Day 03 的单测可以直接测 `draw`，完全不用起服务。

## 4. 记（5 min）

progress.md 写一行，例如：
`Day 02 | ✅ | 手工打了 5 个接口并记录 3 种错误码 | 原来报价不查库存是设计，不是 bug`

## 验收清单

- [ ] 能不看文档说出 4 个端点
- [ ] 亲手拿到过 `INVALID_INDEX` 的响应体
- [ ] 画出了 draw 的调用链，并标出哪一步有副作用
- [ ] 能解释 `_LOCK` 为什么必须存在

## 面试口径

> 我把被测服务按"读/写"分了两类：`/api/draw` 有副作用，必须串行加锁；
> `draw()` 本身是纯函数，所以单测直接调它，不用起服务。
> 结构上先把"纯逻辑"和"副作用"分开，测试才好写——这是我这个仓库最重要的一条设计。

## 卡住了怎么办

| 现象 | 处理 |
| --- | --- |
| `Address already in use` | 换端口 `--port 8198`，并同步改后续命令 |
| PowerShell 里 JSON 引号被吃掉 | 用单引号包 JSON，或改用 `curl.exe` |
| 中文乱码 | `chcp 65001` 或 `$env:PYTHONUTF8=1` |
