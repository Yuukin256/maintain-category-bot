from datetime import date

import pywikibot
from pywikibot import editor as editarticle
from pywikibot.tools.formatter import color_format


class BaseCategory():
    def __init__(self, site: pywikibot.Site, title: str, month_parent=None, year_parent=None, seperater='/', toc=None):
        self.site = site
        self.title = title
        self.name_date_sep = seperater

        self.year_cats_parent = [title + '|{year}']
        if year_parent:
            self.year_cats_parent.append(year_parent)
        self.month_cats_parent = [title + seperater + '{year}年|{year}{zfill_month}']
        if month_parent:
            self.month_cats_parent.append(month_parent)

    def __repr__(self):
        return self.title


class YearCategory(pywikibot.Category):
    def __init__(self, base: BaseCategory, year: int):
        self.year = year
        self.basecat = base
        self.newtext = ''
        self.parent_cats = [p.format(year=year) for p in base.year_cats_parent]

        super(YearCategory, self).__init__(base.site, f'{base.title}{base.name_date_sep}{year}年')

    def get_newtext(self):
        if not self.newtext:
            self.make_newtext()
        return self.newtext

    def make_newtext(self):
        text = '{{Hiddencat}}\n'
        text += '{{前後年月カテゴリ}}\n'
        for c in self.parent_cats:
            text += f'[[{c}]]\n'

        self.newtext = text


class MonthCategory(pywikibot.Category):
    def __init__(self, base: BaseCategory, year: int, month: int):
        self.year = year
        self.month = month
        self.basecat = base
        self.newtext = ''
        self.parent_cats = [p.format(year=year, month=month, zfill_month=str(month).zfill(2)) for p in base.month_cats_parent]

        super(MonthCategory, self).__init__(base.site, f'{base.title}{base.name_date_sep}{year}年{month}月')

    def get_newtext(self):
        if not self.newtext:
            self.make_newtext()
        return self.newtext

    def make_newtext(self) -> None:
        text = '{{Hiddencat}}\n'
        text += '{{前後年月カテゴリ}}\n'
        for c in self.parent_cats:
            text += f'[[{c}]]\n'

        self.newtext = text


def make_list(site: pywikibot.Site) -> tuple:
    base_categories = [BaseCategory(site, 'Category:Wikifyが必要な項目'),
                       BaseCategory(site, 'Category:外部リンクがリンク切れになっている記事'),
                       BaseCategory(site, 'Category:雑多な内容を箇条書きした節のある記事', seperater=' - '),
                       BaseCategory(site, 'Category:出典を必要とする記事',
                                    toc='{{CategoryTOC3\n||人|タグに没年記入ありの人物記事|\n||音|音楽作品に関する記事|\n}}'),
                       BaseCategory(site, 'Category:出典を必要とする記述のある記事',
                                    'Category:出典を必要とする記事/{year}年{month}月|***',
                                    'Category:出典を必要とする記事|****',
                                    toc='{{CategoryTOC3}}'),
                       BaseCategory(site, 'Category:出典を必要とする存命人物記事',
                                    'Category:出典を必要とする記事/{year}年{month}月|**そんめい',
                                    'Category:出典を必要とする記事|***そんめい',
                                    toc='{{CategoryTOC3}}'),
                       BaseCategory(site, 'Category:出典皆無な存命人物記事',
                                    'Category:出典を必要とする存命人物記事/{year}年{month}月|*',
                                    'Category:出典を必要とする存命人物記事/{year}年|*',
                                    toc='{{CategoryTOC3}}'),
                       BaseCategory(site, 'Category:独自研究の除去が必要な記事',
                                    'Category:出典を必要とする記事/{year}年{month}月|*とくしけんきゆう'),
                       BaseCategory(site, 'Category:特筆性の基準を満たしていないおそれのある記事',
                                    'Category:出典を必要とする記事/{year}年{month}月|*とくひつせい')]

    basecat = pywikibot.bot.input_list_choice('カテゴリを選択', base_categories)
    pywikibot.output(f'「{basecat}」を選択')

    year = 0
    while True:
        year = int(pywikibot.input('年を入力'))
        if year > date.today().year or year < 2010:
            pywikibot.output('有効な年を入力してください')
        else:
            break

    parent = YearCategory(basecat, year)
    children = [MonthCategory(basecat, year, m) for m in range(1, 13)]

    return parent, children


def post(page: pywikibot.Category) -> bool:
    original_text = page.text
    new_text = page.get_newtext()

    while True:
        pywikibot.output(color_format(
            '\n\n>>> {lightpurple}{0}{default} <<<', page.title()))
        pywikibot.showDiff(original_text, new_text)
        choice = pywikibot.input_choice('この変更を投稿しますか', [('はい', 'y'), ('いいえ', 'n'), ('エディタで編集する', 'e')])

        if choice == 'n':
            return False
        if choice == 'e':
            editor = editarticle.TextEditor()
            as_edited = editor.edit(new_text)
            if as_edited:
                new_text = as_edited
            continue
        if choice == 'y':
            page.text = new_text
            page.save('Botによる: [[User:YuukinBot#作業内容2|カテゴリの整備]]')
            return True


def main():
    site = pywikibot.Site(user='YuukinBot')
    site.login()

    while True:
        parent, children = make_list(site)
        post(parent)
        for page in children:
            post(page)

        choice = pywikibot.input_choice(f'{parent.title()}関連の整備が完了しました。他のカテゴリで続行しますか', [('はい', 'y'), ('いいえ', 'n')])
        if choice == 'y':
            continue
        if choice == 'n':
            break


if __name__ == "__main__":
    main()
