import os
import random
import sys
import time
import pygame as pg

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の個数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)  # こうかとんの向きを表すタプル

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        合計移動量sum_mvが[0,0]でない時，self.direをsum_mvの値で更新
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        
        if sum_mv != [0, 0]:
            self.dire = tuple(sum_mv)

        if self.dire in __class__.imgs:
            self.img = __class__.imgs[self.dire]
        
        screen.blit(self.img, self.rct)
class Explosion:
    """
    爆発エフェクトに関するクラス
    """
    imgs = [
        pg.image.load("fig/explosion.gif"),
        pg.transform.flip(pg.image.load("fig/explosion.gif"), True, False)
    ]

    def __init__(self, center: tuple[int, int]):
        """
        引数 center:爆発の中心座標
        """
        self.images = self.imgs
        self.image_index = 0
        self.image = self.images[self.image_index]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.life = 30  # 爆発の表示時間

    def update(self, screen: pg.Surface):
        """
        爆発を描画する
        引数 screen:画面Surface
        """
        if self.life > 0:
            screen.blit(self.image, self.rect)
            self.life -= 1
            self.image_index = (self.image_index + 1) % len(self.images)
            self.image = self.images[self.image_index]



class Score:
    """
    スコア表示に関するクラス
    """
    def __init__(self):
        """
        フォントの設定
        文字色を青に設定
        スコアの初期値の設定
        文字列Surfaceの生成
        文字列の中心座標：左下
        """
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.score = 0
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)

    def increment(self, point: int = 1):
        """
        スコアを増加させる
        引数 point: 増加させるポイント
        """
        self.score += point

    def update(self, screen: pg.Surface):
        """
        スコアを画面に描画する
        引数 screen: 画面Surface
        """
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.img, self.rct)




def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    beam = None
    
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]  #爆弾リスト
    clock = pg.time.Clock()
    tmr = 0

    score = Score()  # スコアを表示する

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beam = Beam(bird)
        
        screen.blit(bg_img, [0, 0])
        
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                # bird.change_img(8, screen)
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH/2-150, HEIGHT/2])
                pg.display.update()
                time.sleep(5)
                return

        for i in range(len(bombs)):
            if beam is not None:
                if bombs[i].rct.colliderect(beam.rct):
                    bombs[i] = None
                    beam = None
                    bird.change_img(6, screen)
                    score.increment()  # スコアを1増やす
        
        bombs = [bomb for bomb in bombs if bomb is not None]

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        if beam is not None:
            beam.update(screen)
        for bomb in bombs:  # 爆弾の更新
            bomb.update(screen)
        
        score.img = score.fonto.render(f"Score: {score.score}", 0, score.color)  # スコアを画面に表示する
        screen.blit(score.img, score.rct)

        pg.display.update()
        tmr += 1
        clock.tick(50)




if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()