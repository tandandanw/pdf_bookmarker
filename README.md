# pdf_bookmarker.py

以 test.pdf 为例子，演示一下脚本使用方法。

sample pdf : test.pdf.

## 移除书签 Remove bookmarks

```shell
> pdf_bookmarker.py -r test.pdf
The bookmarks have been removed in test_bookmark_removed.pdf
```

## 给书签文件增加缩进 Add Indents to bookmark file

```shell
> pdf_bookmarker.py bookmark_no_ident.txt
The indents have been added to bookmark_no_ident_indents_added.txt
```

## 增加书签 Add Bookmarks

```shell
> pdf_bookmarker.py test_bookmark_removed.pdf bookmark_no_ident_indents_added.txt 0
The bookmarks have been added to test_bookmark_removed_bookmark_added.pdf
```

## 查看提示 Usage

```shell
> pdf_bookmarker.py
Usage:

Add Bookmarks
         pdf_bookmarker.py [pdf] [bookmark_txt] [page_offset]
Remove Bookmarks
         pdf_bookmarker.py -r [pdf]
Add Indents
         pdf_bookmarker.py [bookmark_txt]
```

# 注意 Attention

- 如果 pdf 文件原本就带有书签，请先使用移除书签的功能。

  If the original pdf file contains bookmarks (you don't want them), please use remove bookmarks function before add new bookmarks.

- 如果想要使用自动增加缩进的功能，请在每级别标题开头遵循 x.x （二级标题）或 x.x.x （三级标题）格式书写书签文件（一级标题无要求）。

  The format of bookmark_txt file looks like below. The `x.x` or `x.x.x` (leftmost of a line) is required.

  > 1 First level
  >
  > 1.1 Second level
  >
  > 1.1.1 Third level

- 增加书签时，请注意最后一个偏移值，应设置成正文开始的地方（因为一般页码都是对正文开始地方而言的）。标题后的偏移值可以为负。

  page_offset must be set and the page number (rightmost number of a line) can be negative.

# 参考引用

- https://github.com/pmaupin/pdfrw/issues/52
- https://www.zhihu.com/question/344805337/answer/1116258929