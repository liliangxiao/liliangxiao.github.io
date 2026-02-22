---
layout: post
title: "An Advanced Look at the C++ expansion methodology of C: Object Memory, Symbol name and inheritance "
date: 2026-01-12 12:00:00 -0500
tags: [01_Software]
---
# C++ Object Model (Based on g++ Compiler): Underlying C Equivalent Mapping of Inheritance, Name Mangling, and Operator Overloading

The g++ compiler adheres to the Itanium C++ ABI standard. Its underlying implementation reduces C++ object-oriented features into C-language `struct` memory layouts and global function calls with a `this` pointer.

## I. Name Mangling

g++ does not directly link C++ overloaded or member functions. At compile time, it encodes the scope, class name, and parameter types into the function name to generate a globally unique symbol.

**g++ (Itanium ABI) Core Encoding Rules**:
`_Z` (start) + `N` (nested scope start) + `length + name` + `E` (scope end) + `parameter type abbreviation`

* **C++ Declaration**: `void Derived::f()`
* **g++ Mangled Symbol**: `_ZN7Derived1fEv` (`7` = length of Derived, `1` = length of f, `v` = void parameter).
* **Underlying Equivalent C Signature**: `void _ZN7Derived1fEv(struct Derived* const this)`

---

## II. Operator Overloading

Operator overloading is syntactic sugar. The compiler statically maps intuitive arithmetic or assignment expressions to ordinary member function calls with special mangled symbols. This mechanism does not alter object memory layout (unless the operator is declared `virtual`).

### 1. Itanium ABI Operator Encoding Rules

The Itanium ABI uses fixed two-letter abbreviations for operators:

* `+` is encoded as `pl` (plus)
* `=` is encoded as `aS` (assign)
* `==` is encoded as `eq` (equal)

### 2. Code and Underlying Mapping

**C++ Source Code**:

```cpp
class Vector {
public:
    int x, y;
    // Overload + and =
    Vector operator+(const Vector& rhs) const;
    Vector& operator=(const Vector& rhs);
};

void test() {
    Vector v1, v2, v3;
    v1 = v2 + v3; // Concise syntax
}

```

**g++ Equivalent C Code**:

```c
struct Vector { int x; int y; };

/* Equivalent C function for Vector::operator+(const Vector&) const */
/* Mangled: _ZNK6VectorplERKS_ (K=const qualifier, pl=plus, RKS_=reference to const self type) */
struct Vector _ZNK6VectorplERKS_(const struct Vector* const this, const struct Vector* rhs) {
    struct Vector temp;
    temp.x = this->x + rhs->x;
    temp.y = this->y + rhs->y;
    return temp;
}

/* Equivalent C function for Vector::operator=(const Vector&) */
/* Mangled: _ZN6VectoraSERKS_ (aS=assign) */
struct Vector* _ZN6VectoraSERKS_(struct Vector* const this, const struct Vector* rhs) {
    this->x = rhs->x;
    this->y = rhs->y;
    return this;
}

/* C++: v1 = v2 + v3; underlying C expansion */
void test_c() {
    struct Vector v1, v2, v3;
    
    /* 1. Execute operator+, generating a temporary object */
    struct Vector temp = _ZNK6VectorplERKS_(&v2, &v3);
    
    /* 2. Execute operator=, assigning the temporary object to v1 */
    _ZN6VectoraSERKS_(&v1, &temp);
}

```

---

## III. Single Inheritance

Base class data is located at the absolute starting address of the object memory, followed immediately by derived class data. Base and derived classes share the same virtual table pointer (`_vptr`).

### 1. Memory Layout (g++ 64-bit)

```text
[ Derived Instance Start Address ]
|----------------|
| [ Base Part ]  |
|   - _vptr      | --> Points to Derived vtable (records _ZN7Derived1fEv address)
|   - Base::a    |
|----------------|
| [ Derived ]    |
|   - Derived::b |
|----------------|

```

### 2. Code and Underlying Mapping

**C++ Source Code**:

```cpp
class Base { public: int a; virtual void f(); };
class Derived : public Base { public: int b; virtual void f() override; };

```

**g++ Equivalent C Code**:

```c
struct Base { void** _vptr; int a; };

struct Derived {
    struct Base _base; 
    int b;
};

void _ZN7Derived1fEv(struct Derived* const this) { /* ... */ }

/* Polymorphic call: pb->f() */
(*pb->_vptr[0])(pb);

```

---

## IV. Virtual Inheritance

The virtual base class is forced to the **very end** of the object memory. Accessing the virtual base requires indirect addressing via the virtual base offset (`vbase_offset`) stored in the virtual table.

### 1. Memory Layout (g++ 64-bit)

```text
[ Left Instance Start Address ]
|----------------|
| [ Left Self ]  |
|   - _vptr_Left | --> Points to Left vtable (records vbase_offset)
|   - Left::l    |
|----------------|
| [ Top Shared ] | <-- Physically placed at the bottom
|   - _vptr_Top  | 
|   - Top::t     |
|----------------|

```

### 2. Code and Underlying Mapping

**C++ Source Code**:

```cpp
class Top { public: int t; virtual void f(); };
class Left : virtual public Top { public: int l; };

```

**g++ Equivalent C Code**:

```c
struct Top { void** _vptr_Top; int t; };

struct Left {
    void** _vptr_Left;
    int l;
    struct Top _top;
};

/* C++: pLeft->t = 1; */
/* g++ specification: vbase_offset is stored at _vptr[-3] */
long vbase_offset = (long)(pLeft->_vptr_Left[-3]); 
struct Top* pTop = (struct Top*)((char*)pLeft + vbase_offset);
pTop->t = 1;

```

---

## V. Multiple Virtual Inheritance

The object contains multiple intermediate base class `_vptr`s and shares a single virtual base class at the bottom. Polymorphic calls rely on `vcall_offset` and special `Virtual Thunk` functions to adjust the `this` pointer.

### 1. Memory Layout (g++ 64-bit)

```text
[ Bottom Instance Start Address ]
|----------------|
| [ Left Part ]  | <-- pLeft points here (offset 0)
|   - _vptr_Left | --> Points to Bottom primary vtable
|   - Left::l    |
|----------------|
| [ Right Part ] | <-- pRight points here (static positive offset)
|   - _vptr_Right| --> Points to Bottom secondary vtable (contains Virtual Thunk address)
|   - Right::r   |
|----------------|
| [ Bottom Self] |
|   - Bottom::b  |
|----------------|
| [ Top Shared ] | <-- Located at the very end of memory
|   - _vptr_Top  | --> Points to virtual base specific vtable (records vcall_offset)
|   - Top::t     |
|----------------|

```

### 2. Code and Virtual Thunk Mapping

When `Bottom` overrides `Top::f()`, executing `Top* p = new Bottom(); p->f();` requires the passed `this` pointer to be negatively adjusted back to the `Bottom` starting address.

**g++ Equivalent C Code**:

```c
void _ZN6Bottom1fEv(struct Bottom* const this) { /* ... */ }

/* g++ Virtual Thunk (_ZTv0_n24_N6Bottom1fEv) */
void _ZTv0_n24_N6Bottom1fEv(struct Top* this_ptr) {
    long vcall_offset = (long)(this_ptr->_vptr_Top[-3]); 
    struct Bottom* real_this = (struct Bottom*)((char*)this_ptr + vcall_offset);
    _ZN6Bottom1fEv(real_this);
}

/* Polymorphic call fetches Virtual Thunk address via vtable */
(*p->_vptr_Top[0])(p); 

```

---

## VI. Core Mapping Rules Summary

1. **Member Mapping**: Objects are transformed into nested `struct`s; methods are transformed into global functions with `this` as the first parameter.
2. **Name Mangling**: Ordinary functions and operators (`+`, `=`) are re-encoded into globally unique symbols via ABI rules.
3. **Operator Overloading**: Code-level `v1 = v2 + v3` is statically transformed into nested global function calls.
4. **Single Inheritance Polymorphism**: Function pointers are retrieved and called via array indexing on the `_vptr` at the object's head.
5. **Virtual Inheritance Addressing**: The absolute address of the trailing virtual base class is calculated dynamically using `vbase_offset` from the `_vptr` table.
6. **Multiple Virtual Inheritance Polymorphism**: The virtual table stores `Virtual Thunk` trampoline function addresses, dynamically adjusting the `this` pointer at runtime via `vcall_offset` to match the actual owner of the overriding function.

# C++ 对象模型 (基于 g++ 编译器)：继承机制、Name Mangling 与运算符重载的底层 C 等效映射

g++ 编译器遵循 Itanium C++ ABI 标准。其底层实现将 C++ 面向对象特性降维转化为 C 语言的 `struct` 内存排布与带 `this` 指针的全局函数调用。

## 一、 名称修饰 (Name Mangling)

g++ 不支持直接链接 C++ 重载函数或成员函数。它在编译期将作用域、类名与参数类型编码入函数名，生成全局唯一符号。

**g++ (Itanium ABI) 核心编码规则**：
`_Z` (起始) + `N` (嵌套作用域开始) + `名称长度+名称` + `E` (作用域结束) + `参数类型缩写`

* **C++ 声明**：`void Derived::f()`
* **g++ Munged 符号**：`_ZN7Derived1fEv` (`7`=Derived长度, `1`=f长度, `v`=void参数)。
* **底层等效 C 签名**：`void _ZN7Derived1fEv(struct Derived* const this)`

---

## 二、 运算符重载 (Operator Overloading)

运算符重载本质是语法糖。编译器将直观的算术或赋值表达式，静态映射为带有特殊 Munged 符号的普通成员函数调用。此机制不改变对象的内存布局（除非运算符被声明为 `virtual`）。

### 1. Itanium ABI 运算符编码规则

Itanium ABI 使用固定的两个字母缩写表示运算符：

* `+` 编码为 `pl` (plus)
* `=` 编码为 `aS` (assign)
* `==` 编码为 `eq` (equal)

### 2. 代码与底层映射

**C++ 源码**：

```cpp
class Vector {
public:
    int x, y;
    // 重载 + 与 =
    Vector operator+(const Vector& rhs) const;
    Vector& operator=(const Vector& rhs);
};

void test() {
    Vector v1, v2, v3;
    v1 = v2 + v3; // 极简语法
}

```

**g++ 等效 C 代码**：

```c
struct Vector { int x; int y; };

/* Vector::operator+(const Vector&) const 的等效 C 函数 */
/* Munged: _ZNK6VectorplERKS_ (K=const修饰词, pl=plus, RKS_=引用到常量自身类型) */
struct Vector _ZNK6VectorplERKS_(const struct Vector* const this, const struct Vector* rhs) {
    struct Vector temp;
    temp.x = this->x + rhs->x;
    temp.y = this->y + rhs->y;
    return temp;
}

/* Vector::operator=(const Vector&) 的等效 C 函数 */
/* Munged: _ZN6VectoraSERKS_ (aS=assign) */
struct Vector* _ZN6VectoraSERKS_(struct Vector* const this, const struct Vector* rhs) {
    this->x = rhs->x;
    this->y = rhs->y;
    return this;
}

/* C++: v1 = v2 + v3; 的底层 C 展开 */
void test_c() {
    struct Vector v1, v2, v3;
    
    /* 1. 执行 operator+，生成临时对象 */
    struct Vector temp = _ZNK6VectorplERKS_(&v2, &v3);
    
    /* 2. 执行 operator=，将临时对象赋值给 v1 */
    _ZN6VectoraSERKS_(&v1, &temp);
}

```

---

## 三、 单继承 (Single Inheritance)

基类数据位于对象内存绝对首地址，子类数据紧随其后。基类与子类共享同一个虚表指针 (`_vptr`)。

### 1. 内存布局 (g++ 64-bit)

```text
[ Derived 实例首地址 ]
|----------------|
| [ Base 部分 ]  |
|   - _vptr      | --> 指向 Derived 虚表 (记录 _ZN7Derived1fEv 地址)
|   - Base::a    |
|----------------|
| [ Derived ]    |
|   - Derived::b |
|----------------|

```

### 2. 代码与底层映射

**C++ 源码**：

```cpp
class Base { public: int a; virtual void f(); };
class Derived : public Base { public: int b; virtual void f() override; };

```

**g++ 等效 C 代码**：

```c
struct Base { void** _vptr; int a; };

struct Derived {
    struct Base _base; 
    int b;
};

void _ZN7Derived1fEv(struct Derived* const this) { /* ... */ }

/* 多态调用: pb->f() */
(*pb->_vptr[0])(pb);

```

---

## 四、 虚继承 (Virtual Inheritance)

虚基类 (Virtual Base) 强制放置在对象内存的最末端。访问虚基类必须通过虚表中的虚基类偏移量 (vbase_offset) 进行间接寻址。

### 1. 内存布局 (g++ 64-bit)

```text
[ Left 实例首地址 ]
|----------------|
| [ Left 自身 ]  |
|   - _vptr_Left | --> 指向 Left 虚表 (记录 vbase_offset)
|   - Left::l    |
|----------------|
| [ Top 共享部 ] | <-- 物理位置垫底
|   - _vptr_Top  | 
|   - Top::t     |
|----------------|

```

### 2. 代码与底层映射

**C++ 源码**：

```cpp
class Top { public: int t; virtual void f(); };
class Left : virtual public Top { public: int l; };

```

**g++ 等效 C 代码**：

```c
struct Top { void** _vptr_Top; int t; };

struct Left {
    void** _vptr_Left;
    int l;
    struct Top _top;
};

/* C++: pLeft->t = 1; */
/* g++ 规范: vbase_offset 存储在 _vptr[-3] */
long vbase_offset = (long)(pLeft->_vptr_Left[-3]); 
struct Top* pTop = (struct Top*)((char*)pLeft + vbase_offset);
pTop->t = 1;

```

---

## 五、 多重虚继承 (Multiple Virtual Inheritance)

对象包含多个中间基类的 `_vptr`，共享唯一垫底的虚基类。多态调用依赖 `vcall_offset` 和特殊的 `Virtual Thunk` 函数修正 `this` 指针。

### 1. 内存布局 (g++ 64-bit)

```text
[ Bottom 实例首地址 ]
|----------------|
| [ Left 部分 ]  | <-- pLeft 指向此处 (offset 0)
|   - _vptr_Left | --> 指向 Bottom 主虚表
|   - Left::l    |
|----------------|
| [ Right 部分 ] | <-- pRight 指向此处 (静态正向偏移)
|   - _vptr_Right| --> 指向 Bottom 副虚表 (含 Virtual Thunk 地址)
|   - Right::r   |
|----------------|
| [ Bottom 自身] |
|   - Bottom::b  |
|----------------|
| [ Top 共享部 ] | <-- 位于内存最末端
|   - _vptr_Top  | --> 指向虚基类专用的虚表 (记录 vcall_offset)
|   - Top::t     |
|----------------|

```

### 2. 代码与 Virtual Thunk 映射

当 `Bottom` 重写 `Top::f()`，执行 `Top* p = new Bottom(); p->f();` 时，传入的 `this` 必须负向回拨至 `Bottom` 首地址。

**g++ 等效 C 代码**：

```c
void _ZN6Bottom1fEv(struct Bottom* const this) { /* ... */ }

/* g++ Virtual Thunk (_ZTv0_n24_N6Bottom1fEv) */
void _ZTv0_n24_N6Bottom1fEv(struct Top* this_ptr) {
    long vcall_offset = (long)(this_ptr->_vptr_Top[-3]); 
    struct Bottom* real_this = (struct Bottom*)((char*)this_ptr + vcall_offset);
    _ZN6Bottom1fEv(real_this);
}

/* 多态调用查表获取 Virtual Thunk 地址 */
(*p->_vptr_Top[0])(p); 

```

---

## 六、 核心规则映射总结

1. **成员映射**：对象转化为嵌套 `struct`，方法转化为首参数为 `this` 的全局函数。
2. **名称修饰**：普通函数与运算符 (`+`, `=`) 均通过 ABI 规则重新编码为全局唯一符号。
3. **运算重载**：代码级别的 `v1 = v2 + v3` 静态转换为多层嵌套的全局函数调用。
4. **单继承多态**：通过对象首部的 `_vptr` 查表获取函数指针并调用。
5. **虚继承寻址**：通过 `_vptr` 表内的 `vbase_offset` 动态计算末尾虚基类的地址。
6. **多重虚继承多态**：虚表存储 `Virtual Thunk` 垫片函数地址，在运行时通过 `vcall_offset` 动态回拨 `this` 指针以匹配重写函数的真实属主。