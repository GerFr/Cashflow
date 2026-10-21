# Kotlin for a Java developer

Short notes for building Cashflow coming from Java, Maven and Python. Check the official docs for exact, current syntax, especially for Amper, which is still evolving.

## Java → Kotlin

| Java | Kotlin |
|---|---|
| `final String name = "x";` / `String n = ...;` | `val name = "x"` / `var n = ...` |
| `record Money(long minor, String currency) {}` | `data class Money(val minor: Long, val currency: String)` |
| `@Nullable String s` / `Optional<String>` | `String?`; `s?.length`, `s ?: "default"` |
| `sealed interface Result permits Ok, Err` | `sealed interface Result`; `data class Ok(...) : Result` |
| `switch` with patterns | `when (x) { is Ok -> ...; is Err -> ... }` (exhaustive for sealed types) |
| Static helper `Utils.format(m)` | Extension function `fun Money.format(): String` |
| `list.stream().filter(...).map(...).toList()` | `list.filter { ... }.map { ... }` |
| `try-with-resources` | `use { }` |
| Checked exceptions | None; return `Result<T>` or a sealed type for expected failures |
| Threads / `CompletableFuture` | Coroutines: `suspend fun`, `launch`, `Flow` |
| Interfaces + `static` factory | `interface` + `companion object` |

Things to get used to: everything is an expression (`val x = if (a) 1 else 2`), named and default arguments replace builders, and `val` everywhere unless something really must change.

## Multiplatform basics

* `src/` holds common code that runs everywhere; platform code goes in qualified folders (e.g. `src@android/`).
* `expect fun` in common code, `actual fun` per platform — like an interface with one implementation per platform. Use it for the camera, the keystore and file access.
* Keep business logic (connectors, metrics, categorisation) in common code with plain unit tests; the Android part stays thin.

## Compose in five lines

* UI is functions annotated with `@Composable` that describe the screen for the current state.
* State: `var count by remember { mutableStateOf(0) }`; changing it redraws what depends on it.
* Layout: `Column`, `Row`, `Box`, `LazyColumn` (lists), modifiers for size, padding and clicks.
* Custom drawing (the bubbles): `Canvas(modifier) { drawCircle(...) }`.
* Screens get their data from a `ViewModel` exposing a `StateFlow`.

## Maven → Amper

| Maven | Amper |
|---|---|
| `pom.xml` per module | `module.yaml` per module |
| `<packaging>jar</packaging>` | `product: type: lib` (or `android/app`, `jvm/app`) |
| `<dependency>` | `dependencies:` list, e.g. `- org.jetbrains.kotlinx:kotlinx-datetime:<version>` |
| `<scope>test</scope>` | `test-dependencies:` |
| Module dependency | `- ../shared` |
| `src/main/java`, `src/test/java` | `src/`, `test/` |
| `mvn package` / `mvn test` | `./amper build` / `./amper test` |

If Amper can't handle something we need, the fallback is Gradle with the Kotlin DSL (`build.gradle.kts`) and a version catalog (`libs.versions.toml`, similar to a Maven BOM).

## WSL + phone setup

1. JDK: `sdk install java 21-tem` ([SDKMAN](https://sdkman.io/)).
2. Android SDK: download the command-line tools, set `ANDROID_HOME`, then `sdkmanager "platform-tools" "platforms;android-35" "build-tools;35.0.0"`.
3. IDE: IntelliJ IDEA, either the Linux version through WSLg or the Windows version opening the project inside WSL.
4. Phone: Developer options → **Wireless debugging** → *Pair device with pairing code*, then in WSL `adb pair <ip>:<port> <code>` and `adb connect <ip>:<port>`. If WSL can't reach the phone, enable `networkingMode=mirrored` in `%UserProfile%\.wslconfig`.
5. Install a build: `adb install -r <path to the apk>`.

## Resources

* [Kotlin docs](https://kotlinlang.org/docs/home.html) and [Kotlin Koans](https://play.kotlinlang.org/koans)
* [Kotlin Multiplatform](https://kotlinlang.org/docs/multiplatform.html) and [Compose Multiplatform](https://www.jetbrains.com/compose-multiplatform/)
* [Amper](https://github.com/JetBrains/amper)
* [Coroutines guide](https://kotlinlang.org/docs/coroutines-guide.html)
* [Android developers: Compose](https://developer.android.com/develop/ui/compose)
