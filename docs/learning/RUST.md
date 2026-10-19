# Learning Rust for Cashflow

A learning path for someone who knows **Java, Python and a bit of C** and wants to understand, review and eventually write Cashflow's Rust code. Each stage is linked to the milestone where you will need it ([roadmap](../ROADMAP.md)).

**Strategy:** read a little, then immediately build something small *from this project*. Rust pays off when you work with the compiler, not against it: compiler errors are the teacher.

---

## 1. Rust in terms you already know

| Concept | Java | Python | C | Rust |
|---|---|---|---|---|
| Memory | Garbage collector | Reference counting + GC | `malloc`/`free` by hand | **Ownership**: every value has one owner and is freed when the owner goes out of scope. No GC, no manual `free`. |
| References | Any number, anytime | Any number, anytime | Raw pointers | **Borrowing**: either many readers (`&T`) or one writer (`&mut T`), checked at compile time. |
| "No value" | `null` | `None` | `NULL` | `Option<T>`: you must handle `None` before using the value. |
| Errors | Exceptions | Exceptions | Return codes, `errno` | `Result<T, E>` + the `?` operator; no exceptions. |
| Interfaces | `interface` | Duck typing / protocols | Function pointers | **Traits** (like interfaces, plus default methods and generics). |
| Variants | `enum`, sealed classes | `Enum`, unions | Tagged unions | **`enum` with data** + exhaustive `match`. |
| Generics | Type erasure | Type hints only | Macros, `void*` | Real generics, compiled per type ("zero-cost"). |
| Collections | Streams | Comprehensions | Loops | **Iterators**: lazy, chainable, as fast as hand-written loops. |
| Build & packages | Maven/Gradle | pip/uv | make/CMake | **Cargo**: build, test, dependencies, docs, benchmarks in one tool. |
| Concurrency | Threads, futures | asyncio, GIL | pthreads | Threads and `async`/`await`; the compiler rules out data races. |
| Low level | JNI | C extensions | Everything | `unsafe` blocks and FFI, opt-in and greppable. |
| Tests | JUnit | pytest | Ad hoc | Built in: `#[test]`, `cargo test`, tests in doc comments. |

Your C background helps with ownership (you already think about who frees what); your Java background helps with traits and generics; your Python background helps with iterators and closures.

---

## 2. The five ideas that make Rust code readable

This small example is Cashflow-flavoured and complete. It compiles, and its tests and Clippy pass.

```rust
use std::fmt;

/// Debit (money out) or credit (money in) — an enum instead of a sign or a magic string.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Direction {
    Debit,
    Credit,
}

/// An amount in minor units (cents). Never floating point.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Money {
    minor: i64,
}

impl fmt::Display for Money {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}.{:02}", self.minor / 100, self.minor % 100)
    }
}

/// Everything that can go wrong while parsing — callers must handle it.
#[derive(Debug, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    NotANumber(String),
}

/// Parses a German amount such as "-1.234,56" into a direction and an absolute amount.
///
/// `raw: &str` borrows the text (no copy); the result is owned by the caller.
pub fn parse_amount(raw: &str) -> Result<(Direction, Money), ParseError> {
    let s = raw.trim();
    if s.is_empty() {
        return Err(ParseError::Empty);
    }
    let (direction, digits) = match s.strip_prefix('-') {
        Some(rest) => (Direction::Debit, rest),
        None => (Direction::Credit, s),
    };
    let (euros, cents) = digits.split_once(',').unwrap_or((digits, "00"));
    let euros: i64 = euros
        .replace('.', "")
        .parse()
        .map_err(|_| ParseError::NotANumber(raw.to_string()))?; // `?` returns early on error
    let cents: i64 = format!("{cents:0<2}")[..2]
        .parse()
        .map_err(|_| ParseError::NotANumber(raw.to_string()))?;
    Ok((direction, Money { minor: euros * 100 + cents }))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_german_amounts() {
        assert_eq!(parse_amount("-1.234,56"), Ok((Direction::Debit, Money { minor: 123_456 })));
        assert_eq!(parse_amount("45,5"), Ok((Direction::Credit, Money { minor: 4_550 })));
        assert_eq!(parse_amount(" "), Err(ParseError::Empty));
    }
}
```

1. **Ownership.** `raw.to_string()` creates a new, owned `String` that moves into the error value. When that value is dropped, the memory is freed. No GC, no `free`.
2. **Borrowing.** `parse_amount(raw: &str)` only *borrows* the text. The caller keeps ownership, nothing is copied, and the compiler guarantees the text outlives the call.
3. **`Result` and `?`.** Errors are ordinary return values. `?` means "if this failed, return the error now". Callers cannot ignore it by accident, unlike an unchecked exception.
4. **Enums + `match`.** `Direction` can only be `Debit` or `Credit`. `match` must cover every case, so adding a variant later makes the compiler list every place to update.
5. **Traits and `derive`.** `#[derive(PartialEq, Debug, …)]` generates standard behaviour; `impl fmt::Display for Money` is like implementing `toString()`, but explicit and type-checked.

**Reading a signature** — this one tells you almost everything:

```rust
fn parse(input: &[u8]) -> Result<Vec<Record>, ConnectorError>
```

It borrows the file bytes without copying, returns owned records or a typed error, and has no hidden exceptions, no `null` and no global state.

---

## 3. Learning path

### Stage 0 — Setup (1 day)

* Install with [rustup](https://rustup.rs/); add `clippy` and `rustfmt` (`rustup component add clippy rustfmt`).
* Editor: VS Code + **rust-analyzer**, or JetBrains **RustRover** (familiar if you come from IntelliJ).
* Learn the daily commands: `cargo new`, `cargo run`, `cargo test`, `cargo clippy`, `cargo fmt`, `cargo doc --open`.
* Paste the example above into `src/lib.rs` of a new library and run `cargo test`.

### Stage 1 — Fundamentals (2–4 weeks)

*Needed for reviewing the M0/M1 code.*

* **The Rust Book**, chapters 1–10, ideally the [interactive Brown University edition](https://rust-book.cs.brown.edu/) with quizzes that target exactly the ownership misconceptions people coming from GC languages have.
* **[Rustlings](https://github.com/rust-lang/rustlings)** exercises alongside the book.
* Fast-track alternative: Google's **[Comprehensive Rust](https://google.github.io/comprehensive-rust/)**, a multi-day course for experienced programmers.
* Look things up in **[Rust by Example](https://doc.rust-lang.org/rust-by-example/)**.
* **Checkpoint exercises:**
  1. Extend the example: reject more than two decimals; support a trailing minus (`"12,50-"`).
  2. Add a `Currency` type and make adding `Money` of different currencies impossible to write.
  3. Write `fn spend(items: &[(Direction, Money)]) -> Money` with an iterator chain instead of a loop.

### Stage 2 — Build real programs (3–6 weeks)

*Prepares milestone M1.*

* The Book, chapters 11–17: testing, closures and iterators, smart pointers, concurrency basics, trait objects.
* **Command-Line Rust** (Ken Youens-Clark, O'Reilly): builds small CLI tools test-first, which is exactly the style of the M1 command line.
* Crates to get to know: `serde` (serialisation), `csv`, `clap` (CLI arguments), `thiserror`/`anyhow` (errors).
* **Project exercise:** a tiny `cfparse` CLI that reads the Sparkasse sample export (it comes with the connector language in the next PR) with `csv` + `serde` and prints the same JSON as the golden `expected.json` file. If the output matches, you have built the core of milestone M1.

### Stage 3 — Idiomatic and robust Rust (alongside M1)

* **[Effective Rust](https://effective-rust.com/)** (David Drysdale, free online): the "why" behind idioms.
* **[Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)** and the [Clippy lint list](https://rust-lang.github.io/rust-clippy/): what reviewers will point out.
* Testing toolbox: `proptest` (property-based tests), `cargo-fuzz` (fuzzing parsers with random input), `criterion` (benchmarks).
* Storage and formats: `rusqlite` (SQLite), `quick-xml` (camt.053).
* When comfortable: **Rust for Rustaceans** (Jon Gjengset): how experienced Rust developers design APIs.

### Stage 4 — Async, FFI and the app shell (ongoing)

Learn each topic just before its milestone:

| Topic | Resource | Milestone |
|---|---|---|
| Tauri commands, state, events; Rust ↔ TypeScript | [Tauri 2 docs](https://v2.tauri.app/) | M2 |
| WebAssembly components (plugins) | Wasmtime / component-model docs | M3 |
| Python bindings for notebooks | [PyO3 guide](https://pyo3.rs/), maturin | M4 |
| ONNX Runtime from Rust (AI models) | `ort` crate docs | M4 |
| `async`/`await`, Tokio | [Tokio tutorial](https://tokio.rs/tokio/tutorial) | M5 (sync) |
| P2P networking | iroh documentation and examples | M5 |
| Concurrency in depth (optional) | [Rust Atomics and Locks](https://marabos.nl/atomics/) (Mara Bos, free online) | M5+ |

Videos: Jon Gjengset's *Crust of Rust* series on YouTube explains one concept per episode (iterators, lifetimes, smart pointers, async…) by live-coding it.

---

## 4. Cheat sheet: why Cashflow's Rust code looks the way it does

| You will see… | Why |
|---|---|
| `Money { minor: i64 }` instead of `f64` | Exact arithmetic; floating point cannot represent 0.10 exactly. A separate type prevents mixing money with plain numbers. |
| Many small crates in one workspace (`cf-domain`, `cf-store`, …) | Clear boundaries, faster incremental builds, domain logic testable without UI or database. |
| `thiserror` in libraries, `anyhow` in the CLI/app | Libraries return precise error types callers can `match` on; applications just need good messages with context. |
| `#[derive(Serialize, Deserialize)]` | `serde` generates JSON/YAML/CSV conversion at compile time with no boilerplate. |
| No `unwrap()` in library code | `unwrap()` panics (crashes) on errors; libraries must return `Result` instead. Allowed in tests. |
| `#![forbid(unsafe_code)]` in most crates | Memory safety is guaranteed by the compiler; `unsafe` lives only in a few, reviewed FFI wrappers. |
| Enums for states (`Booked`/`Pending`, `Debit`/`Credit`) | Impossible states cannot be represented, and `match` forces every case to be handled. |
| Iterator chains (`.filter().map().sum()`) | Expressive and compiled to loops as fast as hand-written ones. |
| `async` only in sync/networking code | Most of the core stays simple, synchronous code; async is used where waiting on the network dominates. |
| Property tests and fuzzers for parsers | Bank files are untrusted input; random inputs find the edge cases humans miss. |
| `cargo clippy -- -D warnings` in CI | Every warning is treated as an error, keeping the code idiomatic. |

The reasoning behind the larger choices (Rust + Tauri, SQLite, peer-to-peer sync, on-device AI) is recorded in the architecture decision records, which follow in the next PR.

---

## 5. Practising on this repository

1. **Port the connector reference interpreter** (Python, next PR) to Rust. The golden `expected.json` files tell you exactly when you are right. This is the main M1 deliverable, so learning and building coincide.
2. **Implement the duplicate fingerprint** (SHA-256 + UUIDv8) and compare it with the Python output.
3. **Write a fuzz target** for your amount parser and let it run for an hour.
4. **Spike SP-7:** a tiny Tauri app where a Rust command returns category totals and Svelte + D3 draws the bubbles.

Ask for review on every PR. Reading review comments on your own code is the fastest way to learn idiomatic Rust.

---

## 6. Resources

Free unless marked *(book)*.

* [The Rust Programming Language](https://doc.rust-lang.org/book/), the official book ([interactive edition](https://rust-book.cs.brown.edu/))
* [Rustlings](https://github.com/rust-lang/rustlings) · [Rust by Example](https://doc.rust-lang.org/rust-by-example/) · [Exercism Rust track](https://exercism.org/tracks/rust)
* [Comprehensive Rust](https://google.github.io/comprehensive-rust/) (Google)
* [Effective Rust](https://effective-rust.com/) · [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/) · [Clippy lints](https://rust-lang.github.io/rust-clippy/)
* *Command-Line Rust*, Ken Youens-Clark (O'Reilly) *(book)*
* *Rust for Rustaceans*, Jon Gjengset (No Starch Press) *(book)*
* *Programming Rust*, 2nd ed., Blandy, Orendorff & Tindall (O'Reilly) *(book)*
* [Rust Atomics and Locks](https://marabos.nl/atomics/), Mara Bos
* [Tokio tutorial](https://tokio.rs/tokio/tutorial) · [Tauri 2](https://v2.tauri.app/) · [PyO3](https://pyo3.rs/)
* [Standard library docs](https://doc.rust-lang.org/std/) · [docs.rs](https://docs.rs/) for every crate
