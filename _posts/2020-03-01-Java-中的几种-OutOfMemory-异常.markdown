---
layout: post
title: Java 中的几种 OutOfMemory 异常
date: 2020-03-01 19:57:17 +0800
author: dox4
categories: notes books
tags: JVM, 深入理解 Java 虚拟机, 拆书
---

【拆书】：《深入理解 Java 虚拟机》第三版（1）。

主要概括了第二章关于 JVM 运行时内存的内容，包含了各数据区的内存溢出的条件。

## 编译 JDK

这本书的第一章讲的是 JDK 的编译，随着 JDK 的发展，其编译过程也更人性化，在 Linux 上编译的话，根据 `confiure` 命令给出的各种提示把需要的依赖装上就没有什么问题。

我用这个方法在 Debian 10 上编译过 JDK 8 和 JDK 12，更新的 JDK 应该也不会有什么问题。

## JVM 运行时数据区

第二章的内容开始涉及到 JVM 的规范和实现相关的内容，主要是 JVM 的运行时数据区，其分布大致如下：

![JVM 运行时数据区](/assets/images/jvm-rutime-data-area.png)

<center><div class='image-tips'>JVM Runtime Data Area</div></center>

根据上图，JVM 的运行时数据区包含以下 5 个：

1. 堆
2. 虚拟机栈
3. 本地方法栈
4. 方法区
5. 程序计数器

除了最后一个**程序计数器**，其他四个内存区域都可能发生 `OutOfMemoryError` 异常。程序计数器的作用是指示虚拟机要执行的下一条指令，理论上不会发生内存溢出，其概念基本上和 CPU 中的 PC 寄存器是一样的。

### 堆

JVM 堆（Heap）是 JVM 最大的一块内存区域，按照 JVM 规范，所有的类实例和数组，都应该在堆上分配，不过实际的实现中，为了更方便的进行内存回收，也可能出现不是这样的情况。

例如，有如下方法：

```Java
public long before(Date date) {
    // variable `now` is used ONLY in this method
    Date now = new Date();
    return now.getTime() - date.getTime();
}
```

分析变量 `now` 的生命周期，它在进入方法之后创建，在方法返回之前**可以**被销毁。那么这个变量如果直接在栈上分配，随着方法的栈帧出栈而销毁，就可以减少一点垃圾回收的工作。

当然，Java 中的绝大部分实例，还是会在堆上分配的。

在 Hotspot 虚拟机的参数中，`-Xmx` 和 `-Xms` 分别代表堆的最大值和最小值，想要重现此区域的内存溢出，只需要将这两个值设置的小一些，然后不停地分配新对象即可。

### 虚拟机栈和本地方法栈

关于虚拟机栈，

> 在《Java虚拟机规范》中，对这个内存区域规定了两类异常状况：如果线程请求的栈深度大于虚拟机所允许的深度，将抛出 `StackOverflowError` 异常；如果 Java 虚拟机栈容量可以动态扩展，当栈扩展时无法申请到足够的内存会抛出`OutOfMemoryError` 异常。

然而由于 Hotspot 并没有实现虚拟机栈的动态扩展，上述的 `OutOfMemoryError` 实际上几乎不会发生。

想要复现 `StackOverflowError` 异常是比较容易的，可以通过 `-Xss` 减少栈的大小然后调用一个循环递归的方法就可以让虚拟机抛出这个异常。

想要复现 `OutOfMemoryError` 异常，可以通过不断建立线程来实现，但书中也提到，这样得到的 `OutOfMemoryError` 异常并不是栈空间本身空间不够，而是由于虚拟机无法向操作系统申请到足够的内存来建立新的线程。

这种复现方式也有一定的造成系统死机的风险，可以通过建立一个小内存的虚拟机来尝试，我试着在一个内存只有 512M 的 Ubuntu 虚拟机中复现这个情况，但虚拟机直接崩溃我也没能看到终端打印出 `OutOfMemoryError` 的消息，可能还需要一点点运气。

### 方法区

方法区是虚拟机中比较**特殊**（这个特殊是我的评价）的一块内存。

方法区由各线程共享，用来存放被虚拟机加载的类型信息、常量、静态变量、JIT 编译后的代码缓存等数据。

在 JDK 7 和之前的 JDK 中，这个区域的大小可以通过参数 `-XX:PermSize` 和 `-XX:MaxPermSize` 设置。

在 JDK 7 和 JDK 8 的更新中，这个区域已经从内存回收的“永久代”（Permanent Generation）移出（JDK 7 移出了一部分），改为由“元空间”（Metaspace）实现，只要不触碰进程可用内存上限，就不会出问题。

实现方式改变了，设置方法区大小的参数也变成了 `-XX:MetaspaceSize` 和 `-XX:MaxMetaspaceSize`。

既然方法区放置的是类型信息，那么这个区域的内存溢出就可以通过不断地创建新的类型来实现，书中借助了 `CGLib`。书中提到了可以通过 Java 的反射来做，利用 `GeneratedConstructorAccessor` 之类的，不过我还没有研究，不知道具体该怎么做。

方法区有一个比较特殊的区域是字符串常量池，而 `String` 类中有一个 `String.intern()` 方法，可以在运行时将字符串放进字符串常量池，如果在运行时大量的调用这个方法，就可以实现方法区的内存溢出了。

在这里，书中有一段比较有意思的代码：

```Java
public class RuntimeConstantPoolOOM {
    public static void main(String[] args) {
        String str1 = new StringBuilder("计算机").append("软件").toString();
        System.out.println(str1.intern() == str1);

        String str2 = new StringBuilder("ja").append("va").toString();
        System.out.println(str2.intern() == str2);
    }
}
```

这段代码在知乎上引起了[讨论](https://www.zhihu.com/question/51102308)，这个讨论又让本书作者在第三版中“无奈地摊手”。

关于这段代码的运行结果，
> 这段代码在 JDK 6 中运行，会得到两个 `false`，而在 JDK 7 中运行，会得到一个 `true` 和一个 `false`。

究其原因，是因为 JDK 6 在对字符串 `intern` 时，有一步拷贝的操作，而自 JDK 7 开始，这一操作被省略了。

在验证这件事的时候，我又发现了另外一件和 Java 历史有点关系的事情。

### ~~没什么用的豆知识~~

如果去 Oracle 官方去下载 JDK 6，那么得到的结果如同上边所说是两个 `false`。但如果在 CentOS 6 上通过 `yum install java-1.6` 安装 JDK 6 那么得到的结果会是——

一个 `true` 和一个 `false`。

这是因为 CentOS 6 上从源中安装的 JDK 6 是 OpenJDK 6。而 OpenJDK 6 和 OpenJDK 7 是共用一套代码的，它本质上是一个实现了 Java 7 的虚拟机，只不过行为上表现得和 Java 6 一样。

两者的关系如图所示：


![Genealogy of JDK 6 and JDK 7](https://openjdk.java.net/projects/jdk6/images/OpenJDK6-genealogy.png)

<center><div class='image-tips'>Genealogy of JDK 6 and JDK 7</div></center>
{% highlight shell %}
dox4@centos$ java -version
java version "1.6.0_41"
OpenJDK Runtime Environment (IcedTea6 1.13.13) (rhel-1.13.13.1.el7_3-x86_64)
OpenJDK 64-Bit Server VM (build 23.41-b41, mixed mode)
```

可以看到这个信息是属于 OpenJDK 6 的，再加上上边的谱系图，得出一个 `true` 和一个 `false` 的结果也就不奇怪了。

2020 年 3 月 1 日 ~ 4 日整理。

<style>
.image-tips {
  text-align: center;
  border-bottom: 1px solid #d9d9d9;
  display: inline-block;
  color: #999;
  padding-left: 5px;
  padding-right: 5px;
  padding-bottom: 2px;
}
</style>
