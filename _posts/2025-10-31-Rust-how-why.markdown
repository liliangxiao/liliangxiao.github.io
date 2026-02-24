---
layout: post
title: "Rust: Improving on C for Safety, But / Rust：提升了C的安全，但……"
date: 2025-10-31 09:32:20 +0400
description: A deep dive into how Rust improves upon C's memory and concurrency safety for embedded systems, supported by concrete code examples. / 结合具体代码实例，深入探讨 Rust 如何在嵌入式系统中改善 C 的内存和并发安全。
tags:  [01_Software]
--- 

# Rust: Improving on C for Safety, Concurrency, and Efficiency with Limitations
# Rust：在安全性、并发性和效率上对 C 的改进及其局限性

Rust addresses C's core weaknesses by enforcing strict rules at compile time, without sacrificing runtime performance or hardware control. 
Rust 通过在编译期强制执行严格的规则来解决 C 语言的核心弱点，且不牺牲运行时性能或硬件控制力。

### The Three Pillars of Rust / Rust 的三大支柱

| Memory Safety / 内存安全 | Concurrency Safety / 并发安全 | Productivity / 生产力 |
| :--- | :--- | :--- |
| Compile-time checks / 编译期检查 | No data races / 无数据竞争 | Zero-cost abstractions / 零成本抽象 |
| Ownership & Borrowing / 所有权与借用 | `Mutex` & `Atomics` | Enforced Error Handling / 强制错误处理 |
| No manual free or GC / 无需手动释放或 GC | `Send` / `Sync` traits | Cargo & Clippy tooling / 工具链 |

---

## 1. Memory Safety (Compile-Time Prevention)
## 1. 内存安全（编译期防御）

**Judgment:** Rust prevents memory bugs (like dangling pointers) at compile time. 
**判断：** Rust 在编译期防止内存错误（如悬垂指针）。

**Example / 实例：**
In C, the compiler allows returning a pointer to a destroyed local variable, causing a runtime crash.
在 C 语言中，编译器允许返回一个指向已销毁局部变量的指针，导致运行时崩溃。
```c
// C 语言：悬垂指针 (运行时崩溃)
int* get_val() {
    int x = 5;
    return &x; // 危险：函数结束后 x 所在的内存被回收
} 

```

In Rust, the "Borrow Checker" detects the lifetime violation and strictly refuses to compile.
在 Rust 中，“借用检查器”检测到生命周期违规，严格拒绝编译。

```rust
// Rust 语言：直接拒绝编译
fn get_val() -> &i32 {
    let x = 5;
    &x // ERROR: returns a reference to data owned by the current function
}

```

---

## 2. Concurrency Safety (Data Race Prevention)

## 2. 并发安全（数据竞争防御）

**Judgment:** Rust mathematically prevents data tearing between the main loop and hardware Interrupt Service Routines (ISRs).
**判断：** Rust 从逻辑上防止主循环与硬件中断服务例程 (ISR) 之间的数据撕裂。

**Example / 实例：**
In C, a global variable can be read by the main loop and overwritten by an interrupt simultaneously, corrupting the data.
在 C 语言中，全局变量可能在被主循环读取的同一时刻被中断覆盖，导致数据损坏。

```c
// C 语言：潜在的数据竞争
uint32_t counter = 0; 

void hardware_interrupt_isr() {
    counter++; // 危险：如果主循环正好在读取 counter 的一半，数据会撕裂
}

```

In Rust, sharing mutable data across interrupt contexts without explicit hardware-level synchronization won't compile.
在 Rust 中，跨中断上下文共享可变数据时，如果没有显式的硬件级同步机制，将无法编译。

```rust
// Rust 语言：强制使用硬件级原子操作
use core::sync::atomic::{AtomicU32, Ordering};

static COUNTER: AtomicU32 = AtomicU32::new(0);

fn hardware_interrupt_isr() {
    // 安全：硬件级别的原子加法，绝不会被打断
    COUNTER.fetch_add(1, Ordering::Relaxed); 
}

```

---

## 3. Programmer Productivity (Enforced, Clean Error Handling)

## 3. 程序员生产力（强制且整洁的错误处理）

**Judgment:** Rust eliminates silent failures without bloating the code. It forces developers to handle errors cleanly.
**判断：** Rust 消除了静默失败，且不会使代码变得臃肿。它强制开发者干净利落地处理错误。

**Example / 实例：**
In C, developers can easily ignore error codes. To write truly safe C, the code becomes bloated with repetitive `if` statements.
在 C 语言中，开发者很容易忽略错误码。为了写出真正安全的 C 代码，代码会因为重复的 `if` 语句而变得极度臃肿。

```c
// C 语言：要做到安全，就必须写出臃肿的代码
int setup_system() {
    int err;
    
    err = init_power();
    if (err < 0) return err;  // 满屏的重复检查
    
    err = init_sensor();
    if (err < 0) return err;
    
    return 0; // 成功
}

```

In Rust, the compiler forbids ignoring errors. However, using the `?` operator, developers can safely propagate errors with zero bloat and zero runtime overhead.
在 Rust 中，编译器禁止忽略错误。然而，通过使用 `?` 操作符，开发者可以安全地向上传递错误，实现零代码臃肿和零运行时开销。

```rust
// Rust 语言：极度简洁，且 100% 保证错误被处理
fn setup_system() -> Result<(), SensorError> {
    init_power()?;  // 成功则继续；失败则立即中断当前函数并返回错误
    init_sensor()?; // 同样强制检查，但无需写 if 语句
    
    Ok(()) // 成功
}

```

---

## Limitations & Conclusion

## 局限性与结论

**Judgment:** Rust is completely capable of replacing C at the bare-metal layer, but its adoption is severely bottlenecked by the existing C-based hardware ecosystem.
**判断：** Rust 完全有能力在裸机层取代 C 语言，但其普及受到现有基于 C 语言的硬件生态系统的严重制约。

**Example / 实例:** Chip manufacturers (like STMicroelectronics, NXP) provide millions of lines of startup code and Hardware Abstraction Layers (HALs) exclusively in C. Adopting Rust often means rewriting these low-level register definitions from scratch.
芯片制造商（如 STMicroelectronics、NXP）提供的数百万行启动代码和硬件抽象层 (HAL) 几乎完全是 C 语言的。采用 Rust 通常意味着必须从零开始重写这些底层的寄存器定义。

**Conclusion:** Rust represents a massive leap forward in producing reliable embedded software. It trades C's intuitive, unchecked memory access for explicit, compiler-enforced correctness. While the language itself is ready for bare-metal systems, the transition requires overcoming a steep learning curve and the monumental effort of rebuilding legacy vendor toolchains.