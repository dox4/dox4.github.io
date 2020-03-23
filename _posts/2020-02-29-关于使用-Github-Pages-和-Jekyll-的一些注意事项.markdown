---
layout: post
title:  关于使用 Github Pages 和 Jekyll 的一些注意事项
date:   2020-02-29 22:45:10 +0800
author: dox4
categories: notes memo
tags: Github Pages, jekyll, Ruby
---

权作为一些查漏补缺的记录。

搭这个博客用了好几晚上，尽管原本并不需要这么长时间。不过折腾也是人生的一部分，不折腾的人生有什么意思呢。

最后还是用 [jekyll][jekyll-organization] 和 [Github Pages](https://pages.github.com/) 的**官方解决方案**。

这样做的原因有两点，一是可以方便的切换主题，现在用的是 [jekyll][jekyll-organization] 默认使用的 [minima](https://github.com/jekyll/minima)，但以后会变成别的，不过对于选择困难症的我来说……；二是 repo 里保留着原始文档，我可以随便改，比之前用 [Hexo](https://hexo.io/) 时传上去的都是编译后的 HTML 文件，如果我想换个主题，在没有原始文档的情况下似乎没有什么好的解决办法。

当时按照 [Github Pages](https://pages.github.com/) 的指引的进行还算顺利，不过在第 7 步的时候，在 repo 目录下执行：

```
jekyll new .
```

没能成功，并且得到了：

```
Could not locate Gemfile or .bundle/ directory
```

的错误信息。

这是因为 Github 的指引中少写了两步，在执行 `jekyll new .` 之前，需要执行以下命令：

```
bundle init
bundle add jekyll
```

之后，将 `jekyll new .` 替换为以下命令：

```
bundle exec jekyll _3.8.5_ new . --force
```

Github 的指引中只提到了 `VERSION` 是当前依赖的 jeykll 的版本号，但没有说这个版本号需要在前后加上下划线`_`。

以上这些都不是我想到的（毕竟我是第一次用 jekyll），而是来自 stackoverflow 上的[一个问题](https://stackoverflow.com/questions/59913903/bundle-exec-jekyll-new-yields-could-not-locate-gemfile-or-bundle-director)，提问者和我遇到了相同的问题，并且……自己找到了答案。

他在答案中使用的 jekyll 版本是 `_4.0.0_`，这是最新的 jekyll 版本，不过在 Github Pages 的 [Dependency versions](https://pages.github.com/versions/) 页面上，jekyll 标注的版本是 `_3.8.5_`，所以我也就从善如流地改成了这个版本。

---

另外一个要记录的事情是关于 jekyll theme 的。

我原本在 [jekylltheme](http://jekyllthemes.org/) 上找到了一个还挺喜欢的主题，[tale](https://github.com/chesterhow/tale)，而且我最初确实也是使用的这个主题。切换到现在的主题的原因是，对于中文博客来说，post 列表中展示的内容太多了。

我 clone 了 tale 的源码到本地查了一下，这是因为它用于展示的逻辑是取前 30 个单词。英文的取词逻辑显然是不能应对中文的，所以取到的字符要远多于 30 个。

于是就先换成 minima。以后有空了再换成别的吧，说不定我也会自己写一个主题呢笑。

在查 jekyll 的使用信息的时候，顺便了解了一下 [Ruby](https://www.ruby-lang.org/en/) 编程语言。并且在知乎上看到了

```
3.years.ago
```

这样的代码。

在我接触过的编程语言中，能写出这样的代码的，Ruby 是第一个。这使我对这门编程语言发生了兴趣，所以说不定会稍微学习一下。

以上。

[jekyll-organization]: https://github.com/jekyll
