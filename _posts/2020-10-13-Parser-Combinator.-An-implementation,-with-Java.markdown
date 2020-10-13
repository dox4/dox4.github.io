---
layout: post
title:  Parser Combinator. An implementation, with Java
date:   2020-10-13 17:19:05 +0800
author: dox4
categories: notes
tags: Parser Combinator, Compiler Frontend
---

This post descripts one implementation of Parser Combinator with Java.


## Parser Combinator

一般编译器/解释器前端的工作流程是这样的：
```lang=text
             Lexer                 Parser
Source Code -------> Token Stream --------> AST
```

我自己动手写过几个解释器，不过目前还没有完成的，最近工作不忙的时候又起了心思，总得写成一个。不过写Lexer的工作略微有点烦，总觉得自己在重复工作，写着写着就不想继续写了。

那天看到了 Parser Combinator，觉得这个工具很有意思，于是就了解了一下。简单的说，Parser Combinator 就是把上边的工作流程中间生成 Token Stream 部分的工作跳过了，直接从源代码生成抽象语法树。

最开始学着写这个东西是根据 
Jeroen Fokker 的[这篇论文](https://www.researchgate.net/publication/2426266_Functional_Parsers)。

（论文中用的好像是一种叫做 Gofer 的编程语言，不过我找到了一个 Gofer 的解释器，但是论文中的代码并不能运行。那个代码看着很像 Haskell，我也尝试着用 ghc 运行了一下，然而还是不行。）

不过论文还是差不多看明白了，我按照论文用 Java 重写了一遍里边的代码，不过 Java(JDK8) 对函数式编程的支持有点残念，写出来的代码也就不太好看。

在上述论文中，一个通用的 Parser 的定义是这样的：
```haskell
type Parser a b -> [a] -> [([a], b)]
```

这种 Parser 我已经在我的 [fokker95](https://github.com/dox4/fokker95) 中实现过了，这次也不是为了介绍这篇论文，所以描述一个比较简单的 Parser 类型，反正是写给我自己用的，用上边的语法来描述的话：
```haskell
type Parser a -> String -> (a, String)
```

不过因为 Java 里没有元组，String 和 Haskell 中的 String 也不一样，所以实际上还是有点区别的。

## 基本的接口和类型

首先是 Parser，我把 Parser 定义成了接口：
```java
public interface Parser<T> {
    Optional<ParseResult<T>> parse(ParserInput s);
}
```
涉及到的输入和结果类如下：
```java
public class ParserInput {
    private final String source;
    private final Position position;
    static class Position {
        int index;
    }
}

public class ParseResult<R> {
    private final R value;
    private final ParserInput input;
}
```
这里之所以要用到一个 `Position` 内部类，一部分原因是方便扩展的时候记录源码的位置信息，另一个原因就是因为 Java 中的 String 不是 List，也和 C++ 中的 `std::string_view` 有区别，所以使用一个额外的类型来避免在 parse 的过程中避免频繁地拷贝字符串。

## 几个简单的 Parser

有了基本的数据结构，下边就可以写一些基本的 Parser 了

### char
```java
public class CharParser extends AbstractParserCombinator<Character> {
    private final char ch;
    //...
    public Optional<ParseResult<Character>> parse(ParserInput s) {
        if (!s.empty() && s.current() == ch) {
            s.advance();
            return makeResult(ch, s.rest());
        }
        return Optional.empty();
    }

}
```

### one of
```java
public class OneOfParser extends AbstractParserCombinator<Character> {
    private final String set;
    //...
    public Optional<ParseResult<Character>> parse(ParserInput s) {
        if (!s.empty() && set.indexOf(s.current()) != -1) {
            char ch = s.current();
            s.advance();
            return makeResult(ch, s.rest());
        }
        return Optional.empty();
    }
}
```

有了 Parser，加几个简单的 Combinator，
### and
```java
public class AndParser<T, U> extends AbstractParserCombinator<Pair<T, U>> {
    private final Parser<T> a;
    private final Parser<U> b;
    //...
    public Optional<ParseResult<Pair<T, U>>> parse(ParserInput s) {
        Optional<ParseResult<T>> r1 = a.parse(s);
        if (r1.isPresent()) {
            Optional<ParseResult<U>> r2 = b.parse(r1.get().input());
            if (r2.isPresent()) {
                return makeResult(Pair.with(r1.get().value(), r2.get().value()),
                        r2.get().input());
            }
        }
        return Optional.empty();
    }
}
```

or 就略过了。

### many
用来解析`a*`类型的规则：
```java
public class ManyParser<R> extends AbstractParserCombinator<List<R>> {
    private final Parser<R> parser;
    //...
    public Optional<ParseResult<List<R>>> parse(ParserInput s) {
        List<R> rl = new LinkedList<>();
        while (true) {
            Optional<ParseResult<R>> r = parser.parse(s);
            if (!r.isPresent()) {
                return makeResult(rl, s);
            }
            rl.add(r.get().value());
            s = r.get().input();
        }
    }
}
```
### option
用来解析`a?`类型的规则：
```java
public class OptionParser<T> extends AbstractParserCombinator<T> {
    private final Parser<T> parser;
    private final T defaultValue;
    //...
    public Optional<ParseResult<T>> parse(ParserInput s) {
        Optional<ParseResult<T>> optionResult = parser.parse(s);
        return optionResult.map(result ->
                makeResult(result.value(), result.input()))
                .orElseGet(() -> makeResult(defaultValue, s));
    }
}
```

读者可能注意到了所有的 Parser 都不是直接实现 Parser 接口，继承了一个看名字就知道是抽象类的类，这是为了方便在写 Parser 的时候进行链式调用，写起来方便一点。

例如，对于规则`a*b?c`，用构造器需要这样写：
```java
new AndParser(
    new AndParser(new ManyParser(new CharParser('a')),
        new OptionParser(new CharParser('b'), ' ')),
    new CharParser('c'));
```
用工具方法：
```java
and(
    and(many(symbol('a')),
        option(symbol('b'), ' ')),
    symbol('c'));
```
好像好一点了，但似乎也没有好到哪里去，再看看链式调用：
```java
symbol('a').many()
    .and(symbol('b').option(' '))
    .and(symbol('c'));
```
是不是清晰多了。

我还写了其他几个 Combinator，具体的可以去看[我的 repo](https://github.com/dox4/pcomj)。

> **Note**<br>
> 还是因为实现语言是 Java，所以有一些需要注意的地方。因为 String 中的元素是基本类型 `char`，而 ParseResult 由于用到了泛型所以必须是引用类型，这样对于规则 `char*` 来说，其结果就是 `List<Character>`，这不仅不如 `String` 好用，而且还涉及频繁的自动拆装箱操作，所以我针对 `char*` 规则单独处理了一下。解析的过程中使用 `StringBuilder` 来保留每次解析的中间结果最后生成一个 `String` 作为最终结果。

### 一些结论

最重要的结论就是**不要用 Java 写 Parser Combinator，代码太罗嗦了**。

我本来是想用 C++ 写的，不过我 C++ 水平太差了，写起来很慢，为了尽快看到结果，还是先用 Java 写了一遍。自己写完一遍再去用 C++ 写应该会轻松一些。

我倒不是执着于 C++，而是我觉得我要是想写一个脚本语言的话，最好还是用 native 语言去实现。至于为什么会这么想，我也不知道。限定 native 语言的话，选择的余地似乎就没那么大了？

### 测试一下

一般写完 Parser Combinator 想要测试的话，会写一个简单的计算器。上边提到的论文最后是以一个简单的整数四则运算解析器结尾的。

我也写了个计算器测试，不过比论文中的稍微复杂一些，加入了小数和运算符前后的可选空白，还有数值字面量前边的正负号。

不过因为 Java 代码太罗嗦了，我就不在这放代码了，放个截图吧。（为了截图我还在测试代码中写了个 main 函数，各位不要学。）

![Simple Calculator](/assets/images/simple-calculator.png)