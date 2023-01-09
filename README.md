tei_excel_tools
================

<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

## Install

``` sh
pip install tei_excel_tools
```

## How to use

所定のフォーマットを持つExcelファイルを格納した入力パス、およびTEI/XMLファイルの出力パスを指定してください。

フォーマットは以下でご確認ください。

<https://zenn.dev/articles/4a4b3c50745c87>

``` python
input_path = "data/sample.xlsx"
output_path = "data/output.xml"

xml_string = Client.convertExcel(input_path)
Client.save(xml_string, output_path)
```
