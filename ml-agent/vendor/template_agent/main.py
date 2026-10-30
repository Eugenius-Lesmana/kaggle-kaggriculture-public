"""Deterministic template policy; no recorded actions or runtime data files."""
import base64
import zlib
import json

import math
from collections import Counter

TEMPLATE = json.loads(zlib.decompress(base64.b85decode('c-ri}ZL{6BkuLgId{uS6IXc8U;9GO6JdRG18ryQ&&dE$oO{o-nC)Pc(<SWTDlS<{kUxF`N3t%@FNi;z$F6_x9(pHlT>mj?*=$EJe{^b1+KRx{X^2ulH(<kqL{qxVS-oJnK_RW*els1e>qd$G}<I4{ZPd<CX8?JxDn%^}1$)`^qetGr&?T-&H-v9FY)ra;UKfHVS>dmV+fBo!}S3iF8KR!{P{9pg{N%Mby^3%iXAK(7^;qkZs)c&@;`rX41Z{NKC@b1?iK6Ib;_a}dT`03?;zIyxXyBF^s{?gv>$A|y?pO3$5ulVrtmxqgg@_+TKc=Oj+Z~WTWQ^B8__Ba3e^7Sjf-XCB5_2thG@7r&s-Q{oJe|Y%C|CTew+ArLG+n-;4XaQ({*L?cqFR$LbeEs6bmw)pg_3q*QPcMFWc=P`4yN4g2eAce^;U9kKe|dQK@aBgHzv|1+`18v*|EK+9<D@cAt#h)m+{%W3`sD2|zr20(@aDsdUZnjeBcF0+osf<(u0DP8%e%Kf{`!Oel)pdu;`496eg1uWC(}G-#;EogIPUM)-s#!ze)r@vuK3eNGRYgptdN4)PoI4C?91n0Kl#k4r`=}?t*sWWX>a}2AHMvT_L_!2)tZ}+pZe*O@4o-`^FRIbvv0rsxAxz;c&eS{Tw28&(<1Zz^RGVt{&~9$X`lK#39h6R#+px`{OR}4K5rLjm3}&iH;r<B8Gm~I{7Zj{eA-HWyq|7y`{k#X?>$z3f71L$`Tu$U=H)N%e|r1D!|gF_nEdp~4{v||<@Ljdhv1iQ|Lcv1#sl^8&8weZzHa|TKQ)3I$uu)Una0EX@bfPp{?<Omr%EW*aHp&?&RXU_y?t@nrVlmZsnb$AGa$|{*1$}=2%`;GR#>j3cw7U2YL#=kQHpbIxs<A11LMEp4YUZw*>n-zFNa06_+ET0=T99IoJr>zCTyei<L9!cj%%SM7qU@WNoLy5<?J`yE&g1gIP$s7Jyll9_PaXHjQ)r?(@&kV4L6zz$=X-xAOHA=f9oIKJiL4I*}wn2H6VZM)a!?b*ZxNTKD<GnUj5%MpMUW$&wjh`54+s-*;n6u|8Gx51^f8F<ITSL{JZb}`0caLzIgtpt?P|%J>K%W-#>fy4e)o8^<y8h;d|6S-1Z;-!|!{qU$>j%+jl=cyz6ZAKmYOHUVQ%bAHMqh%kGW%tX1}lU-d7|XQKb*H{U-0?H|AR{<C3QaQ$z;d-m+NpAFlRzWCK3<qhfY|M2azC!fjISPUkD-K2?#RqNJF1h)QaBI+Nmn21RA%~bWp#jh?M&Sq*7n$aSNj~0Q?ScHq)5t)Tpa|twfN8_+oZ>w>re>lp2V37aNOwC1um<u*zF4RYJAuh~CU>@+l+?wGCZ&}Sp{llG`kH`mEVN}G7QPCfbid=70@V~4=D7f-4Lr^VE{X?}h^Ok1m(dNResItsT@XKmjs%@!%ptdc|a@(R2+rlpnJ?%&S^zzM*-hjwY#i#01-Tt5Y)O~8(|7XpojCcQG;~(1pi1EM0#V@1(wDL`R>(}kA{g?RqS(gKB4TQIj&i|qP4VP}r>Ae`N*pS%!_rE{+@9tX-DWBIb-?#tx<lE=pfByX+zW&{dFTQ>5RmES_{(3wp^>^}#*Z05v^2^(IAABB9bU&XydH43i%MY*K{Po4df4=(Br(R#Y@d0Gh-sRofUtavsuC&YUcBT}xXZ^>t-|GD@4?nzmc>m%rum0O7xc>6;_4@~(;P$DnC{cB>y75c=uRr|jv)_*2z^_4ApEK_k+^tEd$G`h8;Ed&(4cEVj1%uyy6py3fhp&U9>-gi>-#+{9`IrB@Qv_fgK3RNmUo9Fr`M^<bvWi|hKH9gR8a&y>OX0y%l#{#>&{8<ClwLYM5NurvYeHCzQ9^U*=`;{7y?E?KV2io>s&E&+Dnc3y0n-UiUzI_;ujTmlov+0hcEKkXzrDPX0DkXp)o^Bn8}rRC-oJkPA-W9smyZ|z<3Btk|J|w0BGVJV1==5lnI4ZJV0w-*IrifDv8N5F<#zJuT1gT^lm6)m=7ohiZM9Pd(rE_ibSJ&kyj)i!8>$iaS_-O>h194MUut0Tn*US-lkkd+D$U7MdfufFO@S`OdGveJZfQcrQd+g<9$1Ef^s1Mp@*!9guEpy~<G_s@T1+oarsQ0QO3u8$1X>&oDS0PO=S7&v{52c|h8xiOb<!(*2#fg;$~a%Vi1-i|_aV9q9}SM6IKH6nL&K_>$>>Jp_;j(|iIL$MscHQZ$Z_y;(=*Z_y+U;uraFz`QlqNFaMkH9q&gfq5yH`W_6)LWPC#%B(ktNL8o`5ED;pdSu2DexE0>zqtAK>(Gvm)XkT2(;<Jl;^=6I$MK)6443jBPgP(b=CAC0Tr)3|nL*J@j<ZS{B7p;scUQVrxgYRD_;rK#+i3B5IcYYv6N4CJhh(reUMVrne4Fa}p+iK}sUC6!&v4T!?*nsDud#(hSG+qM46N4utCyY`qP7;t+0J7Cc|)c`FTcqUzKv_7sSUfk{$EBi<D<33s(_tEmWk5>6VdQ>`Hm98pXRl2-NXR6XwrK?JpSLtk3x~g<l>GCR_t4ddut}0z#rR$3a*-qKFuI8b%2yv9l#R8Q~fVtc-QppNgM@rN<%mO(rjJDu9pfpe~P7yy2mmz&Q0aU1`p;h$KWO=c$q(=|gsc9Mrs_4<HGE&!*{Y|hIUr41DnC)+X#q{D)xgOiIQn*NsKTl3*#Bs4!g&A*&DYu3)-V)R8)vE|=d89AFlh7)lQl4HK(Cs5vp^jWdQ6<29f1A=7-)d7zDFr5|k|6LGOz1BtZk>fTX#@ESy)=PMks%hMOO^twkPsH5^a^d3s5bXsAJJwxqs;*liHT+v6#-y%k_s#W7^K%2H>|>n`vkhhts7oq)n6G^CnlOV?SBkn-gxbAIDPR<d7VLf8<LMEHEh%k5$W4A5lmR<yZVZ5YgTqvtSi?<>+!~$VFjBr1$k(PM+RK*z`;sfu)@vpW+*Or<>nB;2n!V%vekf)tqMiK-6qwrt~RXjYkSpO3&R*{D1e@NYfuzplwR@5cAp2mv1-2b+BE13tHRoAk*>&#yGr1Pvr>oQK924_sQO|}9B|zH&Vf+(4n$a-$!a36Ch}?`FK=;XRl2HlRp~MpXI7=FN>`OGb8%)>x~g<l=`t5*R;8;-SCuYvaVAGXy-~^<42Rpf!ixRd_s5A?<NC+HgLuh^NNX4vHw8_C=^if*C}^C~KZ?(B{W>C=AFNQQ6P&IitXC3+tV0&E4t4N4!ivo88oqL89d5N+kJp2=Pm%Tdb?jMunYX6kh)<V?e!4p3)5F5X6RIYq`&$*VDr7E&6tO~PDG>?BP3>PQ!b9?G-%X;xb{r0|XZPY1MI)r^*j{X$yIfvLl)A_#<8kUDIYV9KucRy-VbQZ;OgXvo*{rJ-;2eQvyct$7z&VOb^p41i3y6!VxCFR_6@wfFV(EsE9Gq;w=FA4L`Jrv!F$<}OVikj{b(8mifv6ZzY;HG?fx2T1!qP}y(`Yq~R?}#COCzh&Ri&#+m$@{uDqU5&s&tu4BdgL?rK?JpxiqpWT~)fObeT&d#Z_LG+3LtyUY0IvQb0m@aq@<N$(v4`A|Xt=j#|TUpEVpTR@+)sRg0>sLLOb^SQWA=WL3z5svO1AvX<|D|LoZ}hZeSsE4c5{mU~2jR}{eVmU~1&RusSzmwQ4Xtjw%iSlz<v7FM^gx`ov(>_+P}Ma}8eoL<f8<*n1KN>`PxDqZF}&8l=&>8jFYuG6eaSCy_RUFJH?s&rN9s?uey)0BHrSaP;UjpiEKN*2-qTImTO!Lmq*4zL%eC^;crM=d_N=kiQhtHEkDSXIb!$}@8-<mQcYHAFm`W$Bq;L9%5Ikv{k06e>!(4u0%9)}_!ezB^B+E%EvA4ClM+ucR;@CqzS5G%nCk6^#~+u=H2fx~W<>RqLi|-Bhics&!MhS^6t0DQhKVt)#4#l(mwwR#MhmDfX2$F<cYFH8GsG*taTORl2HlnTvg^(p9CaN|(9Vw<=v#x~g=Ui+!uoRi&#+m$}$iRi&#+SCuZ8(y^*^Rq3kI<yAUfm98pXRl2-NC#up_rK?JpSLtL`x~g<l>GCR_s!CUtt}5LT6)9Ees?t@Z%UqFCm98pXRl3X-DOKsJ(p9C)T#-_ht}0zsy37?Rx++~&x~g<}D^jY`Ri&#+m$@RPDqU5&s&ttvQmWEbrK?Jpxgw=1T~)fObeStss?t@Zt4f!-BBd%_Rl2HlnJZGN(p9CaN|(7Jr7B%jx~g=UD^jY`Ri&#+m$@RvRHds*SCuYrMM_n=s&rN9GFPNjrK?I;l`eBdN>#e5bXDmxSEN*>t4dduE^|dnRl2HlRp~NUq*SG=N>`OGb45y3x~g<l=`vTORHds*SCuYvMM_n=s&rN9GFPP7s&rN9s?z1HNU2I!m98pX=8BZ6bXDo9(q*nlsY+Lst}0#Tij=B!Rq3kIWv)o6N>`PxDqZG^l&W-9>8jFYu1Kj$SCy_RUFM3Es&rN9s?ueyNU2I!m98pX=86<om98pXRl2+tDOKsJ(p9C)T#-_ht}0zsy37?RRq3kIRi(>Zky4eeDqU5&%oQnB>8jFIrORBAQkAYMT~)fw6)9Ees?t@Z%UqFCm98pXRl3X-DOKsJ(p9C)pmePY=-)8bz3h*rDb2@E{$GFi*Jr<d@x`~#zxk+v-+lk>=YRU=XWxGNZzNjy<f~_2KL5JCRdC-w{r=hK-#=NXp&DKr_$5FH*#(5nQzsoa3dE63aQrC#{=>UpfB5k0yNC88zxn*T@BjGivnLn7y}XeCe(!J9aArhn{9e9!_4CWuFW$d?`ysjv_?M3tKE6vP6%ZZ*qO{^11cXC?4B`a=Vk;maAg%%u0>YY#NQ4Nhi1dhrMP!+`$BX;r+78p58FTy+?D0!*$1fq>tP!k%9k+(C6zzD=Hj@f-6PjM$a0j8r4P<$H=@o|8Vun{4XBcXDEpB+b3(3sM$>6XRj!QUPh2s*AWRrh3JXpoU;}I5!UTlSb{QBEx-#!2Ge_w=I-~9UeHMj*frEG!0qM@hOgh3r6n6(mmYz-9D8O7I}J{0ocxDuKR{P>~JC)Z!ObQ`=!NNj~9hQw7!Vo0uSiFb(!tC)<Kgk{`k-x`e$9-LB*;ZVB6%T1o!D81sjDeSokXO+S|8ihZ%{z|Hi@qB>T3P=cutAK=nq;82PM1)mDdPKqoi`{~z{93*va~S{&^Hr8H<v@pqLHVj)oGfHXx)@u)V#0U(i|5^kfiE`40w7FEhr4+k4}f$RlEn*|4AJ1au?9p#LTC))rJ#`<E<70=tis_$)b6v}7ND+g0pCCW>htfPXWt8K_!PVS8GMQsdWxMm-CjVs7+ca}l2bR)#$;uqEEt;yH>OUUFmXb<8dkz;!VaX}?0_uR4v5I}X>noT+b%%Q$BWb10TnJr_#bdF3R+AjPG<)w7nAIgg(*5KO}mkTi-B@<y*QyqM7kPQ!fL{%sNL*<DAo>8KGNzB?Bx$I7cNF~!N6So<hLKi3GD#sYFG)Y3H!8mvjePDJ0O~<RRk*r5e?WX;>GEzWC{9K=;~!D7voA=OnMD1>1tRBs|m@BS>6!w@f~BliEOFwRshdd4QNZfI9+vX_&}}EmVrAkhaPAzPFGt>xfoZ{V$#C{q^n^itS0P?VYgE_G2UZoa!-d|Zf69c42XuD+)=v74$*r@!d4_E*7n|!xG?p14+Xn>D8e4H<2E^3ANShRQ(?qQwkKK%#dj4H@EWDpJUxb0cXFwP#UCHTt2?_Zsj39e2Z*hJgn+mTNC-%3mEZ{xVHJ@ck+7d^5(4`C>py(;`IjGqK*Kse`{MbZG7uxQ-*{$24A+9JJE^!wKt-Oe%XX}KeBF(}=QrLAd4Ao6$OG&z1@^^?%Ox(h;sWC0DlQ-{7n@}TCIE(2U;<#mezWXbXSVH<hb<8fb9NB+mX*&7Zk+G#gFY&(YaS*ux^p0G1%hk`JO>aITi!{KVE2wh*fn;sseSwW`_I4s!`HtHs{%GeN?G29v1><p8x{c!^emI7WuX#)L3qsrbBH^_gwMs|4-F@V>E16z6(6->y}9zmPSD$Hp>p$4ItL(b1`vNGReUrzARGgPvxZ59Hv{2-^jA{FM{QV4ue)9&2oR{2ev~c>kkt6-2@zoxksgt-h3@Kpc(qEdwF!lF(OsvA2^|`5Tp3t3-#~}<UYw5oDvZ1v<GEkJ#XzC=UYw41D$I@h_J9VgBW|GN_$a>OJ;#C>tp^|to(8}}8U2NHmHSaSn!i2Rt;WD|v_ZTeK+?MhPKOAqi1dhrU6t(ax~psX^lg++M=|$-R|Z%NNM*2&a47R?SP82MyDBr=fiFJ)w)I5g60?KaD=9nWk_|%C^WDYaz())Ae0Sn>27z)h)gau6L2&yT1W_3C7U@f#to|Xff$QkA!Nowt2EBMeRQ+_yZ=<F76EV0J3$DeB6DmLHYFG)Y341E}yz-Cr;b5R>B;x>;-|=~O0IWPubqnI&f$LqW(Tk5Y4|IZ4L_6^X-A;MeVGCJ@D`XureKwgF^3eeFFZhZsmoUcJF?~S$zJ@}ay>!$@$*+crXO&<3AA_Y(I|H<^-6X%#Q%)W`;?wP+pY9I*^b2KPtwZUZVic<E!i4RpNRwqaC}G=6N6lips<N=lHu9>*RgFp1I4^1Oj3Qt6$HRD%^HF!Ol8Qs|q+UE~aN#>v>2^uc1)7X0@Lt_6OCRS9gXFrB9**(ZjyJ<<dN|H#8}VwIiVKK~t+;@=xQfd)w%iH~Lfl({x#SR*yYHjNcDrnMzRuI=a`PD2iUGxzck>ufY;U&@0=r`n!hRNhd$d1(Zpdf9d;a{pXDec0B0M>BtT0tT2WP&aE)|<%C5<nm#%t{GDOUZJz^=9l5E)ivac8CjEl0U2AcOQ8Kr{+SpIN{F(KCQ_S%&ErcN2h^1_8t~hf9qDVj2{X{z_oK+XhHjy&y1WT|&hR0vL{UI3O3BUqvL|3GW<{u&ssf(B`T0Whl2%I7Qhiq$Wp!$*Nv>@pvz6cVt~i0Pjx1cgOxpGEzJjVSyCBC<lVkOD{!3U<{93I5so?8E1IxE+pf_%Zf$mbL4es@ubp<LzV0rvUsEPVl*(PX`qS0z`%W`?n1IY&vSvnDi~1<&mP+#YYJ`abfKLyo+KAK0656bjnYe>-`-7W$z7#kE0Y;m6@f-hsFi6HF9nU{w$?CjVfuX;00T-}4AM)nV3>>B`Kfs1fZ;A~e<jrpxI>fgv3R8Jg69K-RX{pG!bUc}BiDf}mg|7vQPS;7(H7mc7lDfb_vlWXY*S#-7KsH6JHhE<)<+C6%Hw7}_JK1VH(0!IW49wgnOsqTq;nmd4iQ!n3FC!sNmtYLePOn>$sXP4eBCgsh!F>2v27Gch;w-iHwCb1&`pu0tQ>YFjkZp=jijq#C9EdwbQGIA9cKndve_g;ZHcHY5t~{f4*7Vt{o_gOYS^AAcI|0WH_@D2wfQdl6m8gZtULZ(h@28?Io2WDZbF|TYr+hQky;qojf7Gty?E5AScFzrMXrjRr&Dn;)j9{qi2!rBW&^MJq7AE&5TS?QuxxB6I7MP*I(F|UgMd#ISdYnfzkl}Zn?t)y#ueOmpUFL<U@Hn>ugN{40Cbz&B@FDYVF()~>n2t=vAT)XO{{KWbrZYUwn=eV+vMut5!~T=wdg;h|HIf~6-fU#NUwNcfp`$rYq)iIM~E}%5xT!}F$=)`Az~{c5hAW45+QPxFW?R#VHJ`AlCWt~+#Z)e9N)kC=)#&$femy}P|4>gy)>vSvA)2uaTa-Q5^oF?VMUR-5g@RpKr!F#B=M#|5%zxB3dFV4*PQ_|Qyg<|NU(cHB5aBjJ2XYg(zyXx^dOPRW{QCivX@@W4uI`@Y^cV-*a7f;ufLLv9Uvo90_MB1E=7%Ff%|U#m1OJy`LGZTI@7jqzQvlJo0*xm{z@`#fKW>$28M>TM6N}HqpT6kTHHGne1<l{UrEOfa56Ypg~P@@k$Y^0rOthJQ7hyyNqb5V0CqwS(u)m0R#D_ff#W<V_~Yv@q-(`wQA>RPS^>414D5;T#TWZ_7#iF<i`Q349F6Y6n<NOpJc7nES>co2afhJ4kd7XJU^@D8G%SjS@32MDurp}*3kk^q&IJdnaF}?Y<sO?LW2HBJ+VDy0&Od;<2A~JoOH=JeF6`dZo}nFjsT|b2*Gp4v1ujBmIHpaP0-_Qg&0GN_K7@vlbTzDm)r1Y7a<|czbs|>nGdXel=jwrWVV{`B+-(Q7iS^P^^QSyupk3A4s<pS*9Y)if6>h!`3x#!p(}i^6QKRRc8tlZZ0_W0OE~9bsRw<Bhic4^ud@sJHiV_REur8Q{S5o3}m;Oo$J90uaY(+yl3Ojp3G*a68qtmf30fLUC7Capf(&Z#?k98bNKqBl4mbIa(HdNJys@hOh8>(tU)va~~%Q`-_j!&)QQ|tKDIzF|IPraQ!;HBHvPFvQd*5B(-$Ar~Ps;iP+Nrt=bF)^%mf4mv?tQcOrA5jFG3JU~_t*}6_xC+Y^*6)f7%s*anxnM%q%W`vD>f?&*4JNPezw-Q~!}{HnFX+XKq8;Av)?G=^9;|tUh2sV)mDe1^qL(fTi|rl4<Z~ep$HG-CDEfp?2nMTQMBTy%?|sz8W!D~~2}_LB(33KGj0UPO8l@L!Sh0pspE>9F+)$1;g!Wew?0_c&!d4(s_r8+>k+AWd4GDJdNQ6DX@>qh5oIOxFEUl7VmoMbCKxg(*x}3qkiEUUWEbCRn@Pp~w3{~}x(u>i+di&Tgz6L`BZ|-B^D4WDiFcZcD)X=y+MFWZljM9sB8=FAEd>{#bH#k0mqQ8==8O?+xnaZ>KK>odfDl$juf{GBE3I|-1dCzc!ZNYo&gT;@6&1&`b9zc}19}>(}TNTp~C`(44OTai^W>_-(g;X12Za6dshZNG_?ykn+=q{w%5nUJ~A3Kny#pqCse3UK-j?^vjba=3ehsPsql2=#z^v0$Ra9>mf?2BJM|KeYIV&mb9JpN+$Zrki1ZMXN@5OQ+3gjQ1)wVEQC$W9PwHTB{&&9@;Q4rBdh90H^lCuzRr;VIo>T%Miaw9udvkJ{(eEc5rrmlRZKF-LvT?9T;P)p?O$zpy;TK)aC&{YaNEA~@pUvs^b|l}rPY@D1Xnknklmb)F3gcJD}pbOzVmqy(eNs!`p?s6PAZo9|bp4<hnp?`(kS1CTv=kY4)YVg(P4_U0L%0)oG|-GzWv_pA8qch8@H_iP0gGQ`3k9XRAKN(hTldNH3UmOL15gjIjw$%Fn%3e(<|rc4V`rbsvli9xy`B(|G&6&3}F_E4Z8k~Reu1&z|jBN6uNUvZWL<ymzG-fxE7eOmKPW{f<@IZJPfaRKZ39H_;~fOVJyy<*fCbb7H+hpi`m2Dw-mq{O56;*0>pg5cww(4uxc4BlS~nf3|_VC5?)VQ+ip=t#BhyZGwXMuy#UQA38^f`+}9Ue&sa`RktlZl*hDCY{$^NjL4%MWbJg5|GEP960->mtKL0!5lO-e}XZ%gQmhG%r(n?^*k4bR=fNMl>F9EWObA-3lUZk=@AJVzmshGEZHRN#n&**3e%qbqup^IP2r4&DKhKxwjdQcgHmLp_;SAstJ)dwg!)~0-A;cgsWW;SP{Ll^YPhQ5x(UN|H6a=1)74O=GEGQA>GV;0@ysQxRbI^(#~8d*UZK@O_Y6naJek{A!SzDbgjEwp&&5wrg;UP_yrg=hDD2nG832(0!+wMK(MW_XaAg>-n#8XbY_kQsUUn1q?3k_%2Q0gRns$0|n))Atk%Cd{PSxM4zbDsUf@#Ji+RLIre9lZq20sc;7t)DGJqCK89s?%kb+@W(mc9bQ_co=kAgqUW7+(<+P(gGrPIHhTm~}(q$FuOkSgdTV6Pzw2Bu`?yDstU}3sY)>5k(YA&7+{d_YJ{Un1ez8L3~BJ^1udz10obhgTX2oQJaC@v&}$MGh3LM&Dw9UH#tK}7g=cMjh{sih8!En&X3}Yf!Mv0D=Ca~HZ0hYM~f1W2-^*G{!X&VVEUR)%i4n=!uPnVw1nJP0lmkg^wRfOU=?@cjWE_3yyC9ElB%&xh2dd|HQp;IIy_1*MMGgM8sm)+G!#ywA*0s+#JUL;HmFE!2)Ke8R7UB=a9|B8<Bc#l@CFr$jv>EiIKqwtotclJ+WAB5yb42q0?V8$DDo#(Ce9U>IUjF?y}NkoyuXsl&Y!IFF4fMT4Gvb}5Gv|I&_|`IYq+LnruQxHb)mi*UuFf7x;RK*N9o1X7?{3}H^R6vaDDBsBr{(pfg|ii(6zj`ny^}2lNw3nm}l-u*Vs(12=~nUD`~3pR8*bUSdjLxQDAXiV@(N2gnbFRmIqb~c5Vx1qgful&<;8-fulTn;Ztx6x`<oQ*Gqxs%Yod2y?80yg0@<(YQ1jJdaWi_OrIu6V?LtdW-he=yT}``xVaOLS`(`FR_#5x??EtCtvv1RTNBK#1$U}OZ3|#Z56}K1@zAsrA3FOhj8k|0%gdv>F2~^RJPww11;_t{V?>yuY>)HWLA`kvN>TRGkSagE$%{=&R0QIAS)ucc28%#C>8LkhS50QMcD6XRcF}>jpSd|zYX_c)gE^b-*mk*cYIu_hS91my%MDQw%-Jbz_<=dFD*-HJsunhfg(cv<C$O+K8er*rcObiB!2y<o^kO0<OrM6)-WZP(u20>CB%YgyJU6eY5Do(L+<NI^aA5cSK7=g+yV_S??Q5ysU*Vf9C2u&S(HeS_N9o1oqS%`}3~R=!Me#SeyO6-Z6P(XiIM8TDda#g~2R)OK?yjUT@g^)PQdpADKt)ArWtJ}k65EY@R`$gGkO;c~igTl@buZg{K7(~v;U*`rMtucsa$+T|qG+(*x2|jm?|p0V-nZ^b3hSP=J49gJtbDfcO5n|`oT>sX?;Eib4q@HDsX5@913o*wWEg)iQVRpeccB2pD8ASyLnE8R2_EywW<s0Yl{Z&IyB`u^@qe{p)rOtih7qI;3rf}93a`peID{Pl)p}Lyb@Ce8<PLyBT%V}=y=rdN+>>i=Db(IORKHj4t=fBX?WIv0ipqy{%9N=3-R@d=AZztIz0$6(v?iDe4Jh#HW!SL%T@9p~)0Y=2e^)5I>gsh65O<Iiz*F=Cgaz=sDzmG*abfvof;1XM@s5s4R{FZQX-G|jB`Z|LktR$|s9|{AbQw@?LM@)1ceSD`BCqU*Xh0QRAbDjc9hF`msnoSJkW9JP`kbnXl$#3%?NX`%mD@{GD0f(~poU_Ssa8Q13#0VnOg%aX(pO;MnfjSQkp4mv>k^e556u-*9Ke#}LAn?m*lmm}*b9fS^m<qOs;bjeTFG^k0fb&&F!@JdO<mN$fqDE6Y~UEAmue42d)~|s1jkv=n`k_GQ*lVm!iIZ%SI7=oQwQzwqx8`@gcZ)VHnQAhD|Y(n>kMOzvMO}Jo#5xfAt7FGqj<faM+k*HEf}xwrAsNZQL%xq>AsroJ7tkzRAw{i&vY{b>ud(;6IidT!JoaYm#)^UTCaPsUX+|2DaIqclQ}Bzt-4!v_v{6}>E{KKxKw(4E-LY@x?6Sk#&vi6J2;CzR2Yjjc6Wl)S@hx1y<^*YqUzqNxK(jathgdnT-WWP;KxIX+l!L~3JFMg!@^#-Ya+(h!rlVv|5QXLVwHltMWsMG5id<qB9vYlLsHgDzzRrG*6Uc5`*0FEeme%HK3d_ZsCQRIX1wmgrIqUwkOESa>t`*}$e7DKqF<oMbijs&1r{|dFl)hMPQ$>Cg<iari~!%?yy|LQ3oENOQ4`WoN;>scz$T=yj@BL7C2)#55rVNor^vJt3`Z-+u8RHbs;zdlw6kc`7=ZY!3hWC&T-Mdm&(OAy(Z{Ky2HEyex|sPRH&T69@EjI`ZuxTNu*eL-09MUvY27M>a~Eq_bFyL0xxtiN)|_(yOP;c3SM!`T&v{#U&h>$10&W75$)AKA3A$=;)!w_%-koX#*RLb2FV^iTg+nD17OF4qrK7^$s=ZZv&#t``<?s~ROIen0tM*pyy$}A+aL+T=7f*qSZ)nr&#S6(3MfJT^d#m=IxxP2t?i|Kf)d^1PdpmIw#SQCwC01vwq59rlx>ej(FBty~Z#orttn_WJ<^%#=12x(BAB$+R*<Y2rIz(Wx;}`p1fB4sDza767_@KkktivoL6Hsi{0V(uvKL76fKYsh{Fp@S=5s46y6_E%LRS}60(W!`psV;{VGIWAdM1YapM<Zeq5#iAmiUGpG9ke_=Y$_gM^2_?b8mKcI%6^UFB_ZPG5y{YoQWPFMfqNn3!XB$FrrZk<7xpM!02E;d3Wb9?dsOVlW|Zz>5*%Vg0c(&2tU(p9hGb76JkmL=G^Z1sZj51VPVz2I+sJCub_9xUR$zBp8@7uu;Yb4$h)6i=JYh?q;BgN-R`xf?*9rj%iB^-%a%T6`Vmt1TNI`a7i|@EmZbwu+0z72JBfvvdJOVsYw{aexUR-y75D@72GK!akNb-T7fXt>WL=xQ@9d6+r?K$K~XlM%`rT52UIb;3yN^lvS^*J*9SAu8#L3#xg28E)ZGL;HNf@4SCvv&{_VcXtS=km?3uU{ihWrGcw62-Wa2ei0f3*ji_x$=%d7mwj6^uhL5E_NyJ5))Z5nP8&s1{1vNj(4kA>|SP>9J~$_tPzn9_@-lG?gbO>a7?0^?1?U>iwewq6duZ<IIzBKkY0gEaEhCLFB}ovo$yFD`ew6A9Gj2Se=i&nHG>FaiX^XOqM>D82O!I8z{zEU^cpY}3WonmI2aNKBcuhEyLp>k<??NKn*^hCS3OpRJ=RfQkjJX<cRZpIO!YNSh={C+M2M(6K}60V5;8vP8$(2*i1fif3=!PN?E2F<nU85g??DYS4yTAf-oq%p1`*7|6hplahDd`W63%c=^)Ry|(qM=T8BhcfiF=rRfeb|$Q-r;g-1ze%lp2P5DM#rQU`Wil9BY0sFmM(F-c=Bg1Twcy#9apgR;whuM>%sYH8=#VYO$EeVfSkIZbP5?mnG!FS*YU{D?jT5r<t2_>d(ls;Vj%4+moCEBMl7N83*YzmB613kJM~93pWCb4a@2Tr+^INXDWa{A0nywaAqQ%F_vo(5d$hsFMg&H`19>EE;Xc0&>&oD5&T9(BGz=w#bymio4(%1-n$lF$L?jICJTK_hK4PfD8B@rcFdJ1YBjQ`)u^IYql;RNDQY#zduh0HSgbyrF=*$oQIN<Tem+>dgIr%r*qmyII03L2s5!M4kC>(st#^A@|Ko1hgi|=PgvWEz)ySe&ql#LME^0NV95a<}zzNsl3OJY%9swv=lR~nw-P~_=1E!nQQxHY1Mi#Z2WbeC)R^yp6Ko7G4SL4MAy>HUhn4+H4$-M8J=KK0;!Y*Em^?EP{wej}i5!>8u=3CwXe*lY^WjwhU*rClpW*IL|$Rt3z8d(7A4k5b$>1uRQt4R)?L`DHC%k2b#;7M2sW{V2tRP&9R@1ALp?Oj{p^bHXY5b!_|2E$2LBa2$ix!iGz1UsQSPHD5!-Ej(=MU~X09G8;9DHdYVbu2+Uu7n`zr6WEswnNv2RX5Xhk*D7A=+d~W^}wM~RKql_X+1Dx6G!PADvi54JXFPFO<~+g@K`=q)!c#=-F>>O-9Ac1xoG6EuUUdRR2?|;xR)*o3zsm`Ep+%L7NpRSzc1IbChv^}Zz>ic>);+vW7n>HBTi#xwjY6wJ>>)a0k$8`bPRP@k~xqkL_}6ZB196MNP_Xzr6Hm#A`v2~j%501oYD}vF}}gAh^(N;NesowFlH*S>N5$2OvU;RoXzw&ixD|CAXo?(A@v}O1I3?z{fDnU|MFvU>Ek-ftqmB~_}LfF|MUd?K1rc(0o4(@AvnF_u`+=*rH?m5o@;j@@?c#wC0q~y6XkfZ*PRKFpx5g@%LNS1fzq!7ay4%W7>o&Jycq#7iU63UjRP~28FB$5XMhPOMCc04wb2=yfoW`1soYv$m=)cEtmvy_dHwVd7?>Vq3>c2nUia&O+|U~W2K6@F;MfuX;|PEWtNu+#MY1PJdiVWcU<Q;?VDKDCQ~`D2lx_z`MZjPge7vA`B`#Q|#LkmZF^2o6Hk`X6SNW#{X6w3t=Y3Sn8*RV#F3u<q-|h}bv3$tVN>d2G*xh~5?EzDEWZc%hBOxmibpGW@kRWg<7gqz*9a^`*vHZMhZW5CW2YCWtl1HZxv{RDq^syP3<);q<UvhD^EY%d|?Wd0!miT@hq`u_h?kuWd%nW6UA5lhu!HGPF7L1UlaF294GlzFUU7ZXmqREiH)Bu_cDZt5)y>wB5{M0o12@#PMkqD8*G`bBPPTh^IfDnN^icz|(=@9zH5ZO8%VmTtFA`&5DZ_JKtMda$x45~D`38T5*rD0HT&OpK3Q98#M5!}o484FHEQIeZDAB|PAVIDIE2%7<<eJV0yDP+5kh`t5B6axOR91|MN%p6mHAt7hW(u^?!lNResM|MX<RzxC1Q~@oRMU8k(Z`jR^2<AsL!xWBWM9iHaf>)h1ehLXEb2XQzgB!?`7{%9&SHTeJzE}y2*bDQ(jRFB#`-YUyhaKvS877nhfIvDkiWkI(ZQ!Ih86Wlyc$hq72yhrP4>w?OOhC*d3R;USXf3LswdjJ@VhUPIGL6&HggOUPrkyw;jT0p&U^<OcI=yU2q008<z`g~uP0C?b#~9Qx28WC>SXxfO!SEI_3pVX)TuD4q$*w<(=G}Ki7T{{YdH4OG$B;;MH@Dl|fcdtO=YsHV%+;h5ns3t8$f8!Gidu~>YBkmW-pl_cC67$@ze&g=LmE|n0RJAX;a=OaOi-KvS?txz2v2reO2@%vKnJ^C8Zy<Zmm#CVg!V0g43U*!VS<;2Z1j4fA{}v2^euT)o&gPVQG|V)diy#E$`T;Eym}ojG(6gu8UV|1klE2eT|x@27)hj<gw%^9t3g7kMYEES1$7TAY)r{k*hM2b8*Uxsb2xA!XD3Zzg<Y5#(nEFBbQw@)NJlkd3062fv3mV&AT_hlfwh;0tnk`p6k~+L;D&0Swgveuq1Z+*eJUdy!eKno5S+h+@aV;fj4<VPkY<D_RuZxbUNypx`UKix+5I5KxMPtz%oraQ##q0QT{4G<E<<f!1}#0m-n=g?r(S3*I6cpcLl*haebR2<C%5tqLsoe8hnF!5K!>kHH-rf!4}{)`UOM93;yZC}@p;pGAkEg&qF_4Sj;;I@%XvFUXtquXjI6+1%gk;ECW_PgV$8KEzg)oJ4JC2vQQssmSljY=GXh{t1?F1ne1DoPI@YAEz+7idBBj}iLRQ@&a$Wh;I$Rjm`Z|J);)0johwn>Pk}ab8`>;A4fEYyu?`@1G49Zph=oXHx2J%VsacYT69q(3ohjd!E4}z>9ka&-`4}z{Bka&f+4}z^Aka&AH4+4d6ce5ab1XsJH*N+$%^~Lk&-+cDF=g+@;wq{0yh-Ne(K_e-^84c^H2O7jbA14oDedRc9S$`$u{Z&L_SFj=y`-K&e*h#F2#2#ZsBz7MwBC#)dYD6?n>w+hZZvqjG4J#OP)|(LtiLUnWG8wzysigkpLJ1|X81N8J#t0?wz<AhaSKL6-L&1<047xF-rvgJ)FzAMlo(hcAxuevB%MS&^RWQg}*i~43DY05*1(hdAU<%j~V1&d~yLgVGcmjUbxTw^`)0u!}#SSbh?!}irONO0{x`WY7#TI^6?5`yA8qWuatbl}os0v63h^~NyfS6Q32zoV&0>l=_c6l%$$#ke;6?w<&58?q;z7Epmz>&^|8c`y(cNbtKa05~z4dTZG5>o5&-D&sb4bblArc`Ix!<`Sl<0BOsH1k~%xl!8v-4VGt+Wp-T(G?Li^L=iunb|ezJWL8w#bUs4#hpKn1EUD0{fKUp!m%^{$KJAI7d9PP;eSAlgNS>2aYCnxbTzW5)u@u_Z;RN-%bHz7$Gl0grI$3bh0uz#C}85hE4Ua2MoheT#Jef>C`lJ3GrkeiSc!y%5QK~=Sl@`*6}R)g+0cJg-Xn!rbs+Dx6DDDOBVg4@;CeGA8o!BvU<^2ZGejYQ?TwU>HG%8RM$Cu|A-}UAGa@<~^^kRhWSe`KURAj1B{eiDrk9e%HOchSxfcnBm&UUoV0d$3N@xuHPpK}Ulu$2C!S80m_f!o71gAzAdQBBNM{)gT5N(J<Bw@M^a7RQN2-dG7d_9z(0}kn}f!>Z@n#2fGtRp1b6lr9evzaO0oStkm$9&G^6H7$}gNAnWbYLWqpHfV?Dr+3JPGEv1m;+cA7$yOX8yO3}91MGGFrzFmwo~KgPsHsFMgl?adB6y1g2hr=w(oxb?AbTR60?m<xN~Z@yM#ej7+`v~yM#ek7+{LFyM)137+{*VdxQZXYP%;GLekv>ygM}VSDn1-<W(oHI(eC$ylD0mHdv<<oCbjh@!bKzPwo8@sC~Zts9@m?H%}Y21{zzT!Ju&!8Uz|5fALJvgmk~+06Gnjh>dol*i~YbXnJeoi_#!s6mWX$Aid&&I_!Cl!+eqF>F~#i5B9B)ES&jphmfdLNWxk$;ZtHzqC`QpV54*nNN`pm?L7b2@_7)&L4xrt^<Rtv5>p|GA+h(OILmE`ONAsNw;g6uO(6lvZPyP8+YAX_!xN3QzdA>vI7qOnrv8g1Koau(?ovm72;c8`*TqjXtSk^%HIjk~3j|P%G)I^svBxRqIrt?0I0Z`fd+$idip0dJymutFcNNGm#vl;GFQEv7nA-h=aoFD0Aj29x;mPBnwgw56=#A0^Az|wqkyxoH!&A7xdh{i93LmA*K_a0{@gzuuguZ*Yh8-99jf{fG%2$m|kLE)&9mdg&Pu1p8U!ACMSUOVQv%!%%5Q0Z=_>=|&2M6Kkr3->XS2!#ko$qbHf%DGsjvn<!$3kGtVtn9yO@||qC5Jqjb1WRmqan@#M@ZzmOE#O|z;KAHJmwbdUFvyYkcVk!dY3{<7*XN4ghN(1F5yrW4wyx%!f|sWA$Er&c_0J<5nVxWB>IppY9MER!UIJ81NM&((xrfr>Os0NK0PMUr(i$<>QVY=FhaiIUHnIL1O6kySPw$?jg;t17KM!}3L9P2YD`h9N!&SI<VUn0DxqMM1Ko&Dnr_>QcrvXY3=XXY<jL%$>2?hQ_PmfDSf<gV$?gX+-ddDRk4C`zL_<v$(F|eLjh!H{5HC(c3r31a0wotMv%D^aN_u-?2Ps+a_NodK!l7C>)Pi)C5E{KSMNtFgG7>5ZD9I`rg*BchtJL$>_zw6fv8+=wJUQeXgy-Ozkookc_$hY>Lsl?o_$i|XN+c86$pKhQGLcuH5EvBPhhXq*6AndpAq_ian0Lbp{HIjk7t$p`k-|;MqaiAufgZ$ygF{q$@shwu;iinDX&sR~=%#_;v_ZTiFx;^m{6&G0!c9pL)+hpukkwr7QTLhIKg=+YW8IU(1}5_%_kcY*e869SCB;CC6M`Wt7!;#DOf=1CnC?A2g@PlE2I)0mV5RMR*f}sT@X~f3&3(}o43Z%y=L5r5FerS)<T-44pb#^~&yEQS2hm0`Jgc380=yQC;SJJjun=hFvttQRgw*A-l3P}C%Svup$t^2`d1WxK4Ca-={G5!hm7o$OsFdscz@BL7zyUTP)6<<ge|HFitRP(HmAq58?+!sQ6@=?-k$39w-5&^786odsT#Z`g$?Y4<+r}q;{V5q96?FEw@>TV|>mC=wV$$QyuxG~b_<US<EGjM_F0$eR;-V@pSL*jGE<#W`i|53}R$M?_(p}1>9S>v!(GzfyI4&rs<PG5>F<j;eCKuoml8^6EX{d9~xLM1pti$Fa=_eUL#bp|5E*hm*JWA;>s?dRt7o!SwI8|tOB?ayH3BiyR3<~n`6N0h5>`;gGR8mM|A^WePf~rxvEHJj09g<Tg9uLO$vO^VivSC;#sE=(u6bh>@8>gEfP$;~-tiO_?=uo)`3Z$t|IS`B0J$;+Oz^k_Vp$QaqhuOivO4!Fa5SzgW3CZ_x7j1J3vuaG(o7h<ph_l2%y@{jrQbs3^Jx+h};P|`E@yFR;N#Qh}4GCG1NOl*`hJ-$nHKHga%#k!6MIn*UoD#O|c5M;RVah<^qfxpbBoe4yLVwwx6B*QxVIYTjlr9H}6n2?&yb~eE_%40R&CSfK$-4_;=N~rE1Yyq<KMeL)l95%O4Gvl1(1whz)0hYjq)X8l5RPe^;=yp}3Wqjigr#SLBatyRueY#29Eqf@OB48pgGY;Ax*RxCd1G}Hg~nQ3G#G{kI$Vx{Bjg+3!<S^bc)oE0KH^o8V~r6Sb$KiFX=<F%sJoENi98)1vf>fok?2Och%Crj*+5Yy2a*L1(k0=c?*b3JtgY$16*5OMHy&6)TQfLegglBzam=rnlZ>+E_0e4{bw2|JMl!t(jIgkyi!VZslY<I7M(I+(NcAFZn6uVHXmHAv1Ldqo>7&62#~-LP!tHS^IOt27vd15=XzIXFH@d23m4x}4g@+S6RP6u@flenDE$>^u5EHQr`+;QOLJUYR?8PY<{c?M7*nH8Z@w8`nDKV~U-GwB{QtEWj(NH9m)rEeF?8e+cXL!g@8Kp~t;-jDPX#7eoKHVJ)mw-iRwPa@yAuJ%HHA)wR#f6u0w^)QzLDU{eQ+uRya-Ft2G<F8_O&ZA9nQ1%CY`pTgsUX*J&=C%HI@{n;5CEbVF9r!&--uM-Fnl4j^P3su8$$2HC|wK=+a1HKXVKkp*zOf(4N&Zk!}ba~8|el2lN+G-0o02@x)>Z>In?+^;*i4YOv`Y61PbBA4|Vg|&ebh4VWG6>b}y(!1}c;ur5A@Au^HK7hyr2pMtn%Nhyp^QB9ZI{o(+kQj-X%2XTN*?{JUo>;E-W>Okfd935CZ->4M<U6%Gyt3o9IfcUa*FoWu%8;49uU9N`=gb&WMJfNB+SAUrK@6?4lKYH08=E?|6Q(G+t(!Ves$&cG?=gZR=%*?%0!#53FpW#Yk0I{Hf?*Rg^Ec###9r4HqNf}$%ZQ&3C=WeSR|piDt=6_g1m*WAs!0wo+eq7bKhbC`1Bq>*d!$4$qA+{|7EI~k0{OvqC*_{pHZa<Machlt3ENQ8*0h(w6!ib#Zrsfa{~*osJmh^vT%h@^%o&x1%f-(<%~CF!{0&CY(9xU|0e&4SK8l(`(mmpl7dW$Jh*)Y->tQ~OIvgOcY1MOILzpr{JU6ck-SnSx>}C{s{u1!W3~tDsCkp$JNz29$7&$sXmCSNeOm)=6$U7nrc_R}JI}(?&_C?st@4`q&J{VW8$Y9SlzDpiokn3P*Z`@@#OZ3Wu>|vB|T+VJaNPl0_xY28XL~7)ut9JP91(5R*h!7~cKdWX}y_VSL$lLN#zv0u*2##n-gZWBg!jXhy?M061Y<e<ck!4f%2CcsOK*Lvo5<Y}SNSX+}5(PW@~ks<c6R1sELT#A3s}uuemq6sy0Iq9NOb)EmarZGogk5cS3=T^1M#UD;uGy6Nr=fdO@=kJ4p<vAs1rH^CyuQkHyp%P=tTlx2S<MSu4Bz({D)CMPdA42*Ef$u7Z0Q?lQf+xqWL$hEy$o18!OXehRKYdaR{H_S!h7^vP8DvG0l*zPIXP(8G0Jz=PA-9qXyN}q$#k({99b{QRsIZDdmb3A+y;59#>T>c*NNgW46k>DNXCOqAn$H(pG8?vH(!%(|57AA3!cI)UEy4^3cHrj(dJ0fImEw~4JX$qgnM&!<o)ef?C79@A>q$xZS<D$K%HRX_U83%4YUYdm8IX!(qGKn^Q@?Mc+V9TL3K72}YIjqK|y99fa8uybI^bY%=6=jnevnXBQyJx|C0R!^|UYv$iI7;%hPe*`hoCZwtb>bv@A?22wuop(>u;D$Q+8Xd6hMtU9vzL>u!)#xNjcjl0b0{c+WkK89Nt3Yr+sJY3{Ap+%pySv{lQ8VtXqcpvyn*&23l5X)q)FKADSWn&Szf0VI<W2sF~-`KJ^qGA><d1$1g5e%$iC2vmlSkJ*$_fQ?3u(G2W|+EB_72~0z;O>xqmbm>d4dTDkyfJ2Y2XEwJazSMiGT?h3s50=tKg&6{B=XP;5W4>u?*9-FXXw0@_7J>5`yG2wi7xP0u(kaWzeK=&8x}DGSJKD#%kCrT2&8>P*p)f_{%9yDYjKmf!@kq8Sb&=xT-o2Nrmld5q!VBPDvCeg-NEiG-j<`suhRB(^(;<kQv;Mnack?+-@8R3wr;LluSXdBdTtLxEBIUbr9}w!4KYJWk8Tm##oSK&R<Zx*Q}@yu#3%5Vrkx(6LED-oz+<JQ5+r{4P#mGw&3FEc40E;impK743n{7wbXK6x;&`>7~y!@Eo8UA<tA9^qKZolJ(u64Gvl1kb<o5{%mmQ3WpSAefMXB!&W$?AnUt7862s7_gTH_&2Zpdxcw3$=J-8)$*zuXtuL9?g(PndnR}ELdz9mikVk3pH@m-*%!ND~9J0c335Tk1T*9F%9G7sI3Wrc+F67zZa21XVI8t56lfV)3$nW7ox|}KMO^=ei{eJFII_y!Jc@_nSKS~qvYlsTRB^<KCaS4a2a9qNnD;$?_m<q=w9Jay%GdFF6BMiG~=ZD!qa6n<VQF?bc@UUCI1Tq&gFB}*b;CQ3WaD-IxM?@hHE_2Lz63D<+cOzwv8Iags=4it5rE%QXwA}%!UmB$gLPC|(_;D~2x*VRKgOM=xok-`bNN-v$3W<U!D~?4Xq0sRpNQ9*Dd$@(VDVwlDMV+vXHDDvG0vll)yT%15w>_GGrlKGmZlv?2;HGFD@i0IwFCYcOSz4jV8-H%M75YXxJ#(}|t8ljvu6@vunN-kjF-ot10viU?3`A&HQ5p_KcOgm7OK2%Y7iWT?fGp)GT@Vy0O)n>bB4l{q!x>a%GrXsAd6Rfzl+0AJ4A#m7KZHfx6G)4pW+3;3mnLa`O>J}}*@wfxZRd1D@27$Sx4ksU9!R;2?fZ`my%Nz;lmg3;kXO=6Q`mkPriVoL11$qe5B1U!d-DC+T~fZ_?UvV=h#?mtt2YK@$o0}BmNz{DO<{QnynYhPo9=Ow*xvNMW(wOY!+pr_vK)FS655D*X%gETDs0Ev3Oy7FDQquIVtYg9fMbIkCFC6R(h*~?xk?uKXdE}NMP4z&$#(Y;woSnB9?Qlm6V{PFxCJu3tJgtz5J}+bCFW2zDJzMF4O(y5!Igm120QUZe7)B>RYk<9ikLpe1jwlx*uE6TURtW{6wcn{89xzYui1k(U6$+slMh9>(JT~E*5O8TPvn%Nh2)-A8x$3}m(I6fL(VqnUJla50Fkf*pX-fCZ~#nHv)EC0LIx77SsbK`0U}{uz`1sc1owxWl=w&>QoOIMq#=9HkK?;JfZ83ww{}3fWBJ3xS}&SmG#K(Q@kW#;ni3|;$+I7dgRD42E@7Z$i^F{;3Vy;NSZTo6=PG8&-J#GGim6+8_fXigLxH!cHBrfcyBR33mc3>unMj4=!a2NGC_*~kJ={aZj&KjRJ<s&QhZPjdXy?H&`2nL?p6NV@rq+oxILM3d4u(S}!jWE`QxqJDK4aDcRR%b8g+n?r-|=j4*a`<c54FOP?njc(K05}EkdF5}zU11_k_a;izF5ORH8%pvB#hEaAE&@3b@18#Re=xc;20goCXyEsR&@-knqmRfbPU49Kp`s>L@a7&f<jj)h}hH41cg1a1h^m^5=x<?!f<THx&#Zuff4IR;*e5{eTMfT<k{UN4K0dpfQ-s)JCYEn@EEMJ9i$h#_-HY~Q2vd%_%qc6Q7O2%4a%PkNXQ$RfVw{ts+>9K2P2U{juCEp(sSWKL1qnYdZTnfNF?-yHBt6~3kG%uH(>Ummo5m21cxvxRpAJek_1at_&O$~3`n>mTY^hMBE>0;l2JaL3+A4|WYi#iJQ5*y?k;X2E7~n=qINXS40OhE4cL#?OP53dB+BX3IT{LCjuUV+6bZfZ)HT>wpvYLBxEc!T-kqbND62g2Xf*6Cq2Vwz2I_8%Odm(1yRg(E#e>l(tWNPDG(tk%U3^7z@(?10pGM%al5qLxh*GFG!&7%rgOoy8`^1fM`A|}JCGX4W;R?E4k#a4roV6tH2n1^hIW70F$EIk4bAsVkC$h%`Q-DY^3Dl)@SDc-U90#knrf`RB{W#+w9aqo}IZBrV#r9l6UI(~jmILy*@zGegiUkGN!C9~f314?PB=Vx2l8Ert`Z_4c8vqGkJLy7(o{%^t=>z#loRW01Argmx@~mo(^h?e}wp|F}Yr6f92w!a?;j8R^Fe5BWBYY(ocSS<@N=)b}i&=>(hFVmotRy^%Sd3<xG3YE}Bc5rKuo50>yv2C88HZHfqQu)9RuVlOEV0=MPFK>2lN<;r-GwCLvGmfni1^j+LHz1+I>PH|?9!`iNenW<I7<?9Oi*7#LP1K(1fIYE>O!ld4bpAoAfuzvS-|VpL7CRGDcd!VSg&C`Iyr#!8tM8u^gT_Ah!CXILh{8ujBuCUEWRT;EA6mAtJ!+8TC9a>rkc%PNJ74tv!;D_9Aqi+_(M@h*a`_|&J+Yh3LAG$K9JpkFo!y=1p$%Zjp%4Bpl|Vlb_@;91stS{0m9t~QT^UPB>7|E-pR3Ol7#loQTk{gLb}C0975$vPETbu^n25XrZ|GswHb%va3d_-yW^0^sF?M1usayKf<abNdoD0+1%s@p_*7t|RyCgjjF3gq9#Fwl5F>Z;bojE06-8mRsYm0H$jGfj?@{`(!(fmA@*YR&lJH1$AWeve8Z6N?bpqirN|#yuUhyDsBTt8iy)8U4#u+Of1pee%@CeBlcZoWdJp?){<skMDhx=e$N%%wTE+mOMW}RTNHx7x;V_pWWy}?k2_X8IMM(PN_tSobTgJCKdG@X+<i#2u!!W~)|R}K&dR|p;tM99Fni*HyotB#H`v0hK145S7#v7I!9Yev9;Oj4MaZtZC*<0yGs5(?8un*<Z;!glJJT)z&=7E)KnI+8kd2-Xqun(fl5Q#6l`4KdW-nn4FK3t`wxlkm?{5{k((HUf1d=QxQ0CKv)kV}PS|VBL}mT*vZe$=ws8H0GCV6-mZ7c@-gr*)FEH?5Q+1>OE_igp7@|VDFiiCSePq+yN3OCBtPXe?Ee2je(ZYOOsGaQu>^_j2&P*TZjl>(avRp&=Alo+DnrdUea|Wm|o$cGWZs0$m$6Pmce^z65~s;j*zU$-XB?0sOj4OKq}@SP4A^i%x}aQ<!5t1hZqZTMs?C>V)Ui+uny(=C!uPh!{YXdn$qL{Bt%UF5xS75$t4msjZ1)ozq&M{CKvHfcqSX@IXaMkqLU^fYGM)Jf~Oe*2^SbhxZuT!h?+uc(>W_J^#f#XdU2AlFJob)hH+;4?H>iFE9u0Eh?+<#qf&^PSZH`GmS*Y%rz?rb-EA=|Ng-+qji9gGx8Q*hGJ?G{O#~u+I#EQ_<aTAv6GbyN5m4wAS*EoC2ps`o83S438Vw@Rix*g_wE>EVWgk0tvj(KuAH)l+)7oHuLx;g)6>FW~)clrKvUc?DTx5;b1}MTnjK!MX7=t1)cI}|t11q$y6G=7^6i#W7aFjP76utNvYP85J*Kf5(ON54kBcyf$G82PvDHU3LnS;0`NyUox3yGURZ`CV26ATF+A^C)#QvJc~-LIv3gBcPBx8Vz34U0rn!^3p;X;=iL8Xlz2P^*6~AgUi&M7p{hPf+aV2^O6%&&ryXkqqR%aY$f~OAo&ngoC;TI^~R%AM0y{!(E?a$wLY4`lEC)K$t_jRtf?lrCK^Cz2seux;zqyR9X*$QqJSS2x;Q>@C7@X>FNtsPLJE+^dRWcIS;1?L2u%DI6ck<hN)oC(Fval3|GORqZ2*@7$NuD9)6-^bq?f`bwu5T&=SDLLYnE1=@fV*NlO!YXvz;}0oMU}XuUK^tjI=q_|kDGK?K6#g=rFYl(R5xA?t8utRp2`M6r&LSZNQ#%Vp7qcPCzt^$kCvs%yoWf$Ah2r0cyji3uj{_Ed!ozSV^czBMT&=26p8yVnV@uDSu6jyiFo5xk@;aiuh;rI=!xm4qBidl+L;wlOv)s*yq*9%H~7snFv|nTAfuv5{bmZD@@Bj@>{;&_c$zm!_G9PT6~(;tz*8k#24z=nz9WkzSf+8an0XlwgWo^jxf`l7iL&K9^3K#1K=iBgG6;tRrMw+9hRGG~3cnk%$|m8YSeGNFf?cEuEpE8KtE6G=~lwrkVassVT0Eb);Bdigko!OS=Suiyl2pN-vZ^Ga5Ob!)TZ3GC;>On)f5ipuJA0Tui4>hYawuufF+yRi=kUgCmi~QN_T)kzN|IziXF4O1WpZFN2bE)fMqjE{yMLG?G1p|M*91-8lOVcby@7BwlK+a(#?z1<f$?<_nHR>~DxUD`y7$(No6wk()tTP$bl`Q77AvhC)^-Mkv(wJ%GB(^Jpj%e3Y}j72EwJ@`m4|p}>8$@$Y#^a1NeN$(FfAWgbmaJfiSH%GPt`&?!hm&#{*#@kXMq>7hems#ajvbkw7fKu1hgn#0TBg6G@M#{?V?(B5+>_w9DOPsxhRx1WzGa#SIy&n_m9@4>vAVC78s^g7m9$jTY$>5bAWb}NnTRs*d8vRi3<x9Tn=v9y^7OYaUvLOe7yEvhTHf}ns*%P74+6bgr;dowBa9CFr@D^Ms5ib2;9DCCSg7u4q_?0W>R$SNo#>e=@7$;nXYBeTY3L1B)}7L*0Wb{~YC{A(X579ah@Zhnw3B_I6=n9Nr_M~*#6Hh8gEpOHhKBnzv*65Jw!BD8g2U`<zSs1Z*GW4mMIqBq0mvmj&Vz&B%%UIRvhfiV>BV_?`BFj}ulQMg7fVgdJN2P{7WNx%o`6<{!nfzf>>3NW@iN37vdNi=-^?Bsxo=n1Rs@nGm9XK0lM#&!pZpt~*)7zPI;n$BTwCU>+S7$MioE>03FEm)M^udpt)fjzvD?+0^m@fb;1kCWmSW%dyT79$zzkuWIm7zqzYM5QDLOynZ=sx`&JfG%P$y#@;`NWzC9Sr{02V?Gbtv{JmH^rHNAU|{|-9~#v#Fd7_;u#YdnD<X)>uLA?~m-*1hh%tN3nETFazeTSoD9H-J=toLpVBqGHg`@Uv$SdOLUNRg+Ffee^x2Ux}VVGumQDq)1*bEk3OLj<Xa=n&vL<;na&{E2N!dABM(I%c6)`Ty(@tqj(;56tBAH~m6Qkgq!a$rg2_0dqFe_*kCa>gJBVHCfOqRQ)Fgr1|tY8V)UT*pzo%(BY$5v0>u41GIZbiTsM)u*e-hwiv$q0<%ULl4qr7FHfmd6ff-#XP}!XE(_n?j~K|0eDm|i}W=y#=&~ops^{%MIj_4N(iM8jN2vIm?@?<F4+|Gj{Hv8kZ9+zCu|3lj8!RT*7VMYhyZAh5PHW2cLxVW3JXZt_M2b<2|5u;>i*KbE{a0|LHQwt^`m5}N~twZ=hdf3ViM##BHo=nY@cdw!1hISgVv9C0c{`1H`s|ow(qDx1)u?Z)_q{c@i?IUTek{23Z6^jw{i`Hlm`hto`g_rw|tb;ASsrQfT1tsyxGI@@msKbgy+0OyGQzNZMJ&^1r-E#kD&8~!19s0TYB><(i@_{1MkXJq<5%+=iU5RjE1i#nqfN_KGPK4QBBBkm~hS|ZR}3yu_GM*kiu(1$Z~jL@E%{eBWSiROy2r+P)0!#{JrGCBne&~K`nbkAF+qA(^-3n*3&~~X4Kk!z$dR*P*7^6GVGQGggnw4$N|Oj!Di}4-ih5OyloFNt0pRhY>#yy5)D`g*-MuMh1u?ih|n>^{2>APW$TN?c1I$it2%rsy0aAIjcDkl7^Mq<B4n4@!y^*5<l|p%qJYii?{20s!e2>o2+dydy%mh*jS;s)Gs+Ft6gZR`r-PB;7iBhgo54^sT_WL#lUwnOIM!p=x4lq6p>G8Wg+kHS)?!fLJS!|51aw1`Ga10xUWg^a_hM{~ojQupi!n-PAS+qkJS3JmNEZtQy(D4K!q~l8_=c5z_Qmr*O==xK|N0MKef}j<+h?Qci~Zibsu*^iugfsMzz(M=%-dyni~ujny&+t%aKU&p0$ju*Tw167k6#RHO(+K~0GbBxEA^#W49sW1&=f~N(qLYcnWrjP1Byxng<yd4N>DI=s{dvvC=RD(G0_Q3r(%-1xu&0-3Su(MP{lC8-xD33Jxn4d1T@R5FmYHrvY9`dI^5Lab?)~LNl06>qmy+d7M0tzTHbfdA@k=pP!FMG6mB?=VSB>NdD2B0_jKQCc?~XeV5`sis5^R|8c{}_D?BvUuVbxqH4n_v#tf=a4h-c!v_qvk3XGWXI>QzyN#b=br2ZpoVrL9HcG`IYq?`^`c0$Ch4%Qk_Qavmed7VQjZ3+tLbq>;bK*7T`c>CT)P%`r(_2tGeDD&EbI}~UHYojNgnP+w@Bo;rM3?tV=5*&7)ZH>97DR7R`26yMybka+H<lLIl7(f#!lymO~Xnt$xFu=f=VL^+SzvS(Jfo8a_sL66L5_(-jHPHjb^>hb-)MS*-0mcl~N#Ei`(Q%vGW}sXrLyuQF80Kb1vTg=rrf@Rq#ZF*eh-Qy;MjgrogR@5l=?q}tXZ5D<lL}dISS1UrWPwK<1PY$N%ve|q<Qw}MnEeK-1{%fBLKb*B=EM|Uq_BX{`cY{X1Ouud9L3K;7TCY!(^MK@J{j1s)Qg{kE-*XgcDZzcxjClyrVBI+9i_kr0lg(Q<1V=yAPpqg2}lAv=`R>bNQIKSP#!q~iDc$LdKQLaQzB*VGG%nTA37Q_qRiSQu6_%|F{C_{sgzmiZ7d`WB<X#FB&{2iL^=uc>BBcfc4uN}8PE&TOBd42Nx`H*O6X9=e0sN=0hFeE14t1Qq2ta<9|TRnon>^y7uCMBkQp`_<csps1l(DqSZwCb+ROT_Tm>c9ktt#o+if4g;P{9<i|;|6rHba0>Fb)N)l7inr$NfVu&gVA&4nOO3)#HY>mcQ)lL_lc&rU*iZ#~Nn!5Is%e5=<X!xvR_Kaj@-y{El&84MaE18)hu;E+pe58J28=F+0rKuCD3(plLO?46D}!2R|N>NnT|-bs_#J5oE7VDAVDA!zKKjR>NVA!gEo4AEYiBGO0D2u@+}D9{M0a`rHIk{8XCN*PE>U`pNTaJx3kLTUYF8HB9~(LKstK$o!$bL2!gicB-5(G$yz-nGumnG~-$kpALIW7+ajj^jJa7(PKAk1}p+j>%u)(uY~W_Lw2yO3+&-QroDa*41Ii`!uKyPLCO+OY1F5=Dt`+mf|c3N-w<%6ik7}+$0JLUIY}6HA`;I%shd*ujmCq8H#mLP-d)3>p}=i*qWIgl#S#UYd}eE&CEP`csnBq-mMi^u_X6q=I+ediiyRW4u-&U$bZ36LI4miz|mqj8|yX#jP_ga!haD(LmhUQV_-aV6kpXh0=FS{h@ss?xbxtm10}ynOfUyxycq#71k@KItX6PX5|s(4TwxT?0}Sp&xG0+|ZxR^Hkr;1A0E|iphKE~(!)R+6hxQ1!fu?&iFf#<t{W_L=SY-mUnRjS8Fopn_X!1KYZj*74xo{BA1I!GmV>I{ER$u~PLNbg!Lis#v?(&Q0&%gQXch8@H_bl%u(^U^tW1I(aelyiLM{hh?o8K5B*nvXMzu^jJdx-!Mw*`p8h<`^u{bWGojR9g&KxSVM+{=nbLaQ4C1Pkl=TI2>lgG-#faAr>5Eg&MXGs;-vl#YnG6GZThhDWIrn}|r5wdEMQrG&D!qjUyDL^CsW#wRKwx{N(MDJ_bx{wJP-;a@4Vn-_bM^J&4EKn+>nDZ$Xzf^ZN=79kXbgDj`feGeS)O^`<!(Cx)B1cTE{0zw~I7qbEgj7gKvCxBNVVM>{sv<nV+aR86<;D?qdWk6!aFYNQYAs5CTUXWWeMKP=ML!PgndxU8HPcx7UqPcpU&ZN7N!U1wDV!VJSnK%X#UQ7m=9E^h~iTUVYEK=x4mJTv#z;ZC)tamULDgg@>H47pHIgJ8)1t&$62P3iF5h9-ibubd!9U=1ZPX{Bh-4)v0#<l<VUrd^6_w#>b@lhaxx?d9dFUpP(Q3lgg0+)Gu-7yLMSE_4BLjD!Cgbz%~(?<ffgwye6Q}WYoZwVwAvKMjR>=OOv<=Z_<YP(eCoAf#51k5+2>`vQlp9+h{#|-H-$^;dS_tGTe(kbcKwp%|LdYS@bUXYNdiDyJ_l=;h=h|j#A!7{ae2IMpM(h>WOxOwZho^vMs@Iu3V6Lp99u@2CVYQgT1PMU@bg0k;5g$sg`UNnXKhDA(QNSI$Ukm)L{Tq=(9a5WV~3CuS#d?Xy>>66eS8LB`+=9@k29(N@ZK@j9K3mITWLIgp%jP1@I#c_rr*G-8=!k{Wj7B*8xEGB{Oi{Ky-vfqfbxk&hc?qe<Ab&mh23j!-;>;!@7%d2Y{vHIU;FuGXFDIT$1Y=6s}_Od$|qJlw_^o&A680!~nz?je=UJ@AU$N>~NpfEE~gjCG>$RQZ3pfD&DJr#8_6y|2;$!&xJFB5GdCn;fcWT+qAcY}<Dg7jmQ-XDs^1Chi+4{2=0{O<S9o_(|4Q)1hg9G22#jjLMIh90W7!wR1}!D&-5Q2D$InFFrgE@FV=B&dW(5r@$xG69`MM)6gsU~l*cF$xV{`syP7MnM9NjG#f{g`FS(&9or+Dl}LL=!i24jhul73tY}abCq;%q2E9Ujzq!fZ-$n~;I<JRpoL+RVXRml&Mb!)4aL*VbTTS7D#9J6$WPq~un2dMUV)0kI+ykAkaCOr6a6CQxE$7El6zRW#mw%QT*KT=yu3=G)ny;ok}>0#1&*0oyND-CAYXose}#EhP4%u4{D|Bx)+wQ(ak27~iEV~vIhmNGfQE(pgT>OKj6oa3D4vB*jNw~^jq<aK%KKc}!@(O6oxaFt4LTgFP9ATDx}R*u{q)PG^t5uvu(tc3%b7USeJ%1b{%igx7UdiZd@%<UKjFspI4QnXZnopCa4hk))NWM{CPPc(HfmXdBE5Cb4+~3ZPgsWY9yvC1#zd;iZUm8y2h6KfyJR%)xe>7#H`YjHoDPYski?LrQoKtOHMqm9iPC`m?Q1y`Hv`hlgdl=EsJ<;cFe@^)Bc+FAQkmTe%F@?Cf_d3j(!=;p6Av>=<#m@)wUYPX!4gfdT4|8p9}$UX1o}lp+*o^fP(qblCrYgAbDgacbD+dL?ac}jJbvWhw4#tWbZA;pNF<PBrH|(=3JG-^bZHroNTA0`9}-^_66VOx#iEd~r`|&sJ3?kRM@YHyNkX&IV`2xNp0F%|>WrdsC)Dnad<_Z{7)ZNE>4K0Dx50js0f~h6CF%l}gOO16ok(xu(ovsbU!Oa*6B_I@?4=7r!raCQG6NF!NHU52k>Gghm34%d5n<LI9#NM!E}c0hCw1t7ope_XU3dgmU41BI=%6F;C|wK=+ub1-^)O>4&kpQi23n;K#UZ7CF7%Mck;OpI7~~?4;yWX;yiF>lc`mA?@Z-<HBCQ52r5MDQBC&hJSVHd{^;GdgaVV&9?ob>O93dAm$oB)XrjC#UDdc<Uqj3oN^Y(CqtSR0LqM+iU$Wrl$tjLGfp)&>t$%?!*Ns5S)G9w`#LHSTr87!*$$Q%uY?N1JdQ;?~oQ@Mt`d2$D<CuPz6QIslv^F+x6nP8HHG$mt_DuWzY9~p2X$%96d6S1Mo3Y?s1sZ5@X7#c8c8woNrbkY%No;;u!D!ZNA;TV5y&Lifh4{C&EaB)99(kOmIoItySkuV{Lg?o>|Xec|uDHwxzNnptOX3zw@bTlK!GNwT=G&m%u7cU76od8CpCPUf<00UH$LA)d|3YwI2G!*to4)q*R;Q7#|KRtw;ntS*}%oOGm5d<_=JvxDP&+<N7gypgYp34pyZFq&Eh+#olpvY1Ql|H3s9Tr6wL*;%k?y4SYFEH?KLLQAdGv%}mTmu8^65~T|b#pBcMU{AZfF=tVYzB;;|0^WXlr$uonpYCdGtfMplFR5;nKZX@8STKNISUPs_*b#M3&uhIRiN==Hy%ws!@t_CV?E8&JOftv)>y3foH6LFvFn@98Ath72b@s`Ec~spXaim%1J=^gGct4-_Tt$24y<me7}ry`Y*MbLF#0l5OH6%oDEcx=uVTPL*^P!rl1}rHLiV&njpAO2Ea%pgs38Hl9RRnBp+PB-TXX7Uwcl?&v(u8j^73(Ys|2>m>67XtcPA&u6uG@>IhoU4fFLRe*BP7c0t7_>!r4X_=!(e%6GMPW{$UPVFj+pw!B$L0OhUp-Id@!`_=@TN4>7~#_2;&fi>H9&&5FZcx@)wwER-<;j`&;6KbC+Co|@~|LFp|WfD4wT8*fH{i>$bSxTuN?h>NbcfVeF4t*(UJmR4OC08KN)uHF?Su640a1C7R0A2M{b^nPVeHUqWz>SF#VW6c{5MF|y{u<nIdJU@jc@5THy1%<~5MKo%Hm(#p@4U7f_qo3k|6*J-y<i3oMqWDRxNVSpNomOD4$?DXd#7LsY%E)vu<oUtCt(@q7iloN81_qYX?Z48&?3lUVjG_rLscDdQ0%ImR$GcVqlIo|-gyCDk!0l(#ari_$nY%Ow^8y_sg4WaJR2JxzDK<YMf#ZG=i;~H_q=uJ+u@JXH{gVL;SyETn!C0hp$f*bmq-d#8AQY3Z^}$G_w8t%-(bqt3z$ji27UnkiV>2LOZ-ZTVD-sMZSYthTPRNkChc9Hx=M2v}8-Zg1Kc?Fs+^yw!l(@f=gsdg2kGMY)2_%`R{6j_Iu-zwep`G(Cjsgd<LUwMHE(i&A8<dC{kkGe5q?-W=Q%<z(U?dWvLpCCf^Cv?nI%GlCxL$g9Bsh*lz!~RubBA1$AvCm&ATy_ZE0{uwfUvG091=XBu-jD+sx{sDp>Eevx)>bft(^Z0W=+aUj$JTel53)~LF>>!FNABr!$B`y3=XDR%0!|h9qI*0=M1TYI{w>-B)RJ7Tv&FZBpp(JN`E?m&iNXu_Zp?w)O%sianOdX99I;~<e4-7yF($$84-Fk6tXHvy8Dy6oNjk0bbTub*z&0ZA4fxRJA{!Np;*$M&vx^NIxh2K{ULH%yxA}w_WXt>IV_5YKfmt6B3UC3#UX(*GMW|F-5J6GoE0}n7lXsi1c7!(Lfyvnz}<1s)l#MgfwC6D?2W^A=O^pn`Mq!msj~NQe|Xk;xgNvMe)s(Och5>qWlD@=YP=B^*~3e_`YRzXsKSxt45=n+2kE=orYhcm?I6AM?nsy!B!Wpr^2mWnD}XR45Z!%}aZsi7njVV6c27t}jX}=WmO?OqjX{I--Z(68BrK?1Y!-;EU4+Y#u!$Q7HC^^DaNs^sG*V5(J`v2=7(fNOM%HZP$zD_&bcN3me3DB@Y(tZ8vF^X+%m{N&GYgppub|8^7*$XJPiZqKJOahn8-k#45R_g#11Nk36u$__ZMqduI0{OCCjwA(1!W3~sh~_ju}eU?N}e87<XJx!pg>$2H^ZFn*BtR;E5ys(9ClhrhP_KXNrz#Bu1gAv6l*AKFiNjTiyAC)Ft%PGPs!jhl>SPxkkSbe5fzaL5m^z55K$G82oYToi4ZY&f(Ra$R6Z5P$f8hr`2e@#p>PMOuN;hcvv&<ctz*vKE8r9cQ!N%f>;$K-?aJ_B|8byeJKPC%`SHrS{!-F_)A>LV6_hC`vVt-NMO9Fypy&$96ckfInSw$Sa9TXA?^s-}kLnBQv3IHT-e>CVCNDTEv5&!+JI5PghXS0_wZD=q0ChGvM1{jxve47n;7}C~W66R}XM@93IE*C=H<_p{fP2~t2oA6<V36J&4m?fSFCpT{-lY&+7TpJDA~Gb;mI-xt7?2F9mtGM!<k)}&?)&QTIU*d78}?U{G{a>cMV$eRf@qPB2Sc784E#9AJrjx}>5QYM1-b?XmTTz05)KB=3e#~kk+jFTh$-3^H-iMKAXD@py#@@7A%_huhey&xlJ^Q855{(;NTs570jm^LAF34CF3?M700Va!o33jy;?CZMJE>@{03G^B(s~95DAx@6NTc+M2Psevtln$JhU3g|V0FGO1!p9+*MBq=35)>|DV$H{L#7VogzJS%0z#HUop3Z1+dU%_S_*}|6b7;ss=&7*fjfKQJa7XNiwx2wL1Avj5!fAy1oD8}fMN-AlDkuHh@1!Gc9|qk2ZbnSpvvtsNs_Y#-!7Bn>7YnplBD5IzFq#v+%ski=8wD)2I3`NP|v5W_oyl|IlZ9A8!R?$B8r6c{Nz*9CcsDtHpFB7I?_!nwEwSO2LV$qwE3=H2LX98wDYZBM>=&7SjjQI{)@>;q7xTK=9^0J#Dz{6U%d_y7F2dXL+^)x`cryok^^Y^E);R+?qd6zqT}J2d#?(Phv()8FE}2adzL`K5%JSOq0VkAauDg}W{uw+iUe;!hOY(3_&g-^T8z?ba^nT_=~9zz?gPb=!yw<yA?jX^VjUv#tj27w5USTh{R|e^m@)U=l|}kP2O}YFV`6RwBoe%#oKxpBAfd`BBsv%geG7!b8E`PSK`ER8iG;b@VPJ+kGo3Ip%1u4OL3(#2X1pLDNtF?a?jEj?Xo?>!kaa|a!U&Pa8)0RyI6riMC0P^h+29Zr4oAoTb~ZQ?n{cz9r8dKX*Ua}zAZx<S3kTL_Io>E84pZS!gq&|V=aX!P19u;XJZH#>yNA=nIKjk$U3?|-2Hd$vXtALp<BgC<XmJ+9{z@`m>1=R_3Wrc+zS7y?P!*0#ICO>M5)M=0xP&9oSF)k&s6CNCl$x-R>o`j94hQZ!_DhK9aqr7lBJZ`IdxQ=<8;&<Z9-+gJ%KepOzS7y?5ETx^$$X`=!J#S~mvAKdN-j)1>29zM1P7FO8l`uK11E6lmq6w#<%I(y>KJd74o9M|<XFV;1G`F&fdoIRJf+QG;Eg&uaFq0ZnK)i_m3EX@@N~dXs8oY_g+Y4poc66mJj*GXcts+;C@E(FN(LkfYSP^WiRCm^>gdMQ+3$~)Td;u{Fa7%`H0FksMzX6ogFt{NjYjE$kVq&-N^hMj3W@DC*&>V;@s6tjYF2|{MWgiYNZ{4!VW`OL<^jp(t~{VCmGxMDv>BK_w({?l=mPBng`DX~3OlAnIpxS#ppa-APTw(}48`sAsqGGhD#r^r8j50SvyTR1yFVmDAVg;ep^{_>iBY;FC=wi^@ZiXOa0Y@xKnKTBdVeUclDC9Zw!64QMbrIL&>s-EBLro96s|zBr6bvdS+w&YtI!PGdBSC=G9F37=969xO=9|^z8q$)1iMkdzMM{)q&JuVjgYT$m*!knvdNPnhNAm{9wmffFHK?c2%HHLlSfHQB#-QSqcD2XL=Oc9LmKdzAQVlj7ZDyk1U7<GLPrmQP6Rz5=0(Ddm!6`C$mz@h1Woz*=m-w5Bz$zF9_DsCM@oAp6NpYI9SN1Nj&$-F5;{5+skgV}kd;xOdUw(k#*Wn6-EQn$h=v*F8BGf<AT)aEh>dO+V`qzI;>_AZzdMmog6U26W(tBKfr*sBpDGB51S(W=lC495NZI_NLys>kgDivu4?Tl)F+im3zB&6vcLyScjW%n7zg+S;@(kb+IE3_bdw4)9s|OU^t-#G6tLARzhcV-|?M*bAnkPb$9`P#(3{k<Lh&X2T0d~jXz>sG_DCi^eI|bpeJ<laV9Jt@op)i?%a2TbF!C|`}bONmindf$i1IgmOAac6#Sr$RGtbZ74idCu1G&poul6gW|E4nklAu1daEIQfd8dBG{9Sn!M5d!c1k<drh2NZ>bIWmJ-6cP!}QBG%hKO{nyxn06UqUb`XoF`y`H8t_sjz@uacX6tA;H>$f-Ej~Vht$YWPUi95aZrbj=qm^aeIxn8-GN9M({w7;NbrDe!BpbSFWg7!Y(yPr?ymVIuSbt&JFRvK@9JhV>CWy-5*H|6xHAI|3DxkCUK?#0wBspIuLtRZkdQYL0ofl3RnDCHgORwESkV4RB*cPpR?=laBEb{72_$CvfKBU_M%-|_ctYmhDu%9fbo<d+@U!d&XW=}5_@mT{GecK3bTT+ZIXmDLEF1<!_l*dkkmWdtM?;|st0vnA4~yfWx($G$geWr<7K5VuMg&kKR1r}J4)=k=%s|naT}48a;v)Zu>jvuR5)Sl_dg=Y4SX@(W_Dhzz@;xNVCQ@DogF%8@kUprskS+N<)B%*;#fKh`No;TWHWU#=?NUWqHd_jH#^=iZm9d}p?x7Gj<KSiNsy#ducr+9#1p}E`0ZVSJ%^N-{xwrO4G~_B*Bt?6zifEU8DI(O4pg`K?Ub+A%LJqk-ydq(W_KGOU+jtpFVd6-~h+-!u2({4cf|SH*+s}fe%eZ-FC2OPMr~cp%P5ZRq@KY}x(a707vV>}98oBi^vyNOkIN~KV=+PkouOsRX!LgDDxH2>>a_I%Bkf~dp{HF{=>g^_mG7!1l(wWf2s39da9U%po7!~E^wp%*Zg!`buUQ*UT8(}XVvB=q*=TKQsmbDK}@cMO7hIB<CCRi3iT$$kI?Zl71ejSwQkJ~5EjE1_muYUs_%p5q>y_1gUqxLX;y6C<@@|5*#a|1fq!_Pv*n;T|kocIe#PS-ix19rzj+y*z!?l{P*7s*>+&Mt}Ffk@bU2}ZRP1Vl=R|5T=OyZd26%}~RNrbj?XGe+s7aR`Z{?9G=vY%BFjKW3bWKr<&XQ1JwsCn8KtC5+11{8KWAX3lo-j4YZ*OgAZ#Mzd@_@q&3Y3C6pW!=x!s5)j&C>rJTIY8c!-b!{Ql9;H{5u4D`hRXhmXqSN6a3uB%=8V^<28RBR>bV1>gqp>iF?*_I1d^8@muyfTucr0!jRQnYXl-)d&Gl;~nhuD?u5|lmj8=+O&8;3(XCJVwrRvc2}MyIk5`X=b-wxQ7AD3CPFW^OIq{ar|i7*Ugq?E}T!3lXwO?c(+{<tNZ6dsBEBbH7Cylnt_sWvDV9iY@~UQ%0js0+Sy>VQt6~vrC5zFW>S}Hi__p)*=d8i!5j@s-U&#w6#!Brcgx%31$%%F$yr^klDj3in4oYNOw41#zrfSoUut#&Kw@JhG7EJRY2z~bjHZ)Met}5z6JzZ1qWB*rAaa}r0XyT+8T-?)^HJOU=EySa-mi9(h)(#E++5nv$Y_Lcfgzy$l|Sz=}`8l$?fbbJSx|Bt;YhT<T+Tb@1-farnQbpU@X^=erXMoz<6nju4$tqHTRUKkeX{y%|n7zb7;q2ab43rLxj6#_8wOWT0Z6<2W<QJ&NLCL?F?meFfW6TV7s{^DE*-@cLWt#6y}bgCx*n_h5D@qTK(xVAocF0Nz7e%!0sr$AT#5j19mUH#N3U4hb$cnmDOTSK_@s_LoXijL+obh@{Y||e{4uU%AKOXBWr7H#sZJy888c}@Hm2|qsS7E_07^D5V8xBLT4Wch*7%08jrHO#&-u|y9Zz+f5=JRK;EGR{h>j+7#udbAfcm<)p$&8=Y{mq5QH=_?&iCK*6($v+VuI2bUl{r{g979s@~77dp|k*KliNdOks(k?gTr&zV(2>Tp17~Fw@B>&h3*tP~b;`aqeFFKnOxsm_6JbReos~`P`Gahq(J31Aaqb6x`KwE<ZS-pyX7sFLfwY?m0p}=Q<df16lNMBI0xPFc1|!bTdhz!vI+LFi4jY_L2MfLFJE%KUYvY(GOBK0s|%iRTjiz6$fZWFK8PSH*nnF;tG||npkuY=v0{>UE`za{?Mt83JD$&i--`M(oi*!VjvMhFI|d9r1tZObkVimWlV)9c$ZEz6@I5q=k+F^a#CbU^+h_Z0!1RAkX~ns68w<m;r0)L>%00W``GxA1Gp>01G(KJ-HlT0UKz6iNng@K=Tk%+5ANnU9@g8v^ur5D%{8U@J;Pu?N;g~;VsUQY<0A<AlaybCPo<l-3bp?@=&AJ55s$+jmalvN%e8!@uQo4)PhxwY-%dmhhn}gn_xTZ&K~VJh5mG2@H+ot{=S$zX2c0h!c)s+~B<>!;MCy>qVGpCnvKqYuLbMdE%_=ITa6VZEEdwm2=%h(nn<=>qWEnlh>d00e3X^9e3I)#|0_E2%NTJY4le9L64yQH<qmY9f&R&{^$syEOgK_yxk0~F;TeH_1z9+9={_X9rA71?U@RwI_UVV7=w!P}_PdY>M;^l`I-AbRlfBEynC*FR2^7h>)-CrKFEdR4loP6RFC!f4}^U447Pqz6VpS=CcCm-IuY;XAHub({p^6LHDA6tVr+RVX<^>^+5@|%|*e$#%^C$C@r`Qh~^Z!hlh!`q*KdHwL=;gjytPdbx#VPpN8+B?1d^ZSQ)|M~FaCqMl3^37i#KKb**hyQwbc+)TW!{2^+c>l?Nz54J|yS$fg#`Uy+{IS1ld&5_6#t-t}`2CBA|Ni0iuRr=#{yTRbr9Z!Z`@{d~t?etn_J3~LtNy=VU;g;+<(n4MCtv?**dDx0)0*rb-oE+p>aV}P{k8o?i&bl`e|h=p-HV@Jy?OEer<XpFHEbi}Z~xk&@qYYmw^zLT_4R{)7(YLJ`01_x&=2n({9^y|@X{mS?I8a7v^&AW&+WH)F&?jnzdr6R!`~nGmErHfrZfERt7l(6|N7%!pZ)H47ytH$FaPD@!=69?(m&F7ui7o{&;GfNAAj+y$0c0+?r|9xzYCUf@%wQ(7r*M4bScv>>vAD}Y3(!k`Q?AN@AWSqe(Fk@x)-t!S}-sE@Z+l=`uF`YF3|z(U;iHA_FsUteE6xw{-?LE+b6=FHj26S$7*Jn;ojW8e)!7=^d66R1UKPKa;sXc6ijL6?ZWI$dIZ8{G_Lz;T92D64c?)DRW2^$>Z$rD2m<0QYP*d*dH3qCKg~*cyVm`0!!N}zK0SH|gXLq(c!bM)v*<D&@9CdyzYH_3#v!YjU?DFT0mA<Hk_0O^9qv{L)@bLJd=byEv;a`oe+4IJ@tnL1d=Z#FJcq2|Qfz#v!&=z*lsQM9a;$_AT8wekG!0{pH_jJ@?ed;S)^E|978oG^*5d%hqW&DyziiDWP&~_23rhR{+PKDtS+A+2S-v(kKCoep3m)8HPZJ&-s3|Qx{)Y=InN{}sx7172WK?u<9eQX{ocD`r?RUeuTl#jeX7LjkUyk8_`M6*?=v2EI{iFTUPY<tuY~3(_yUx`ZU5s$k8l)cm?YHmVJ^b*Y&!YbP^8bDN?$w9Cy?Fes-$>rKZcukf9kgPI*^f8+OY3d47yNYL#E<{<^TW$GFT6)H`YX(zZeRZJ!>{jN{_wZXpLL3H_VK?i)^I5%Bx|+x<9~VYyK~cieDV10xYHkhd+{whQpVxe<IN|vio?G@e($d1G`i^Hzlw`nhTo=PvawP%rjfimF~#?|6qiD4<_xo<aaMJwfd6XWs)rZtoAsi5gfGVHyQ=pK&}Zbjmtk}<*^G<Hs*72&iz(T17jxo^uuju9SXkSeSi=-o%3SkBK|8ONZY{k~Mss7eo7rC>Pp(<KzdE<rg7RkcK9*mj#_din|Cn)$lzP_Vg8T{&JCD;RYp;5lu-n4?`G9%b)b3MGC;14M?(*Zd#8!W2w&d`j<&sTY#{MM}GSP3JLhlwi#)2<dupSrOFv8Q$BH!n7v3z)XV$=}9hR3M~1!(OM=3THSvAw$VE}Bd4LW16fg1rlcdl$_r@51xe!VU$y+?_vqNL>-o)Q8Y|iw~h^eTWA0Auj*VTyr5*_<vVi2<H~L5L#cj5PZgk;MIjF+J*2h`BoRgZi{9t@gPE&vCV(^=~v6{L~k@xmid_eBLBg##T&aAH}+=ZA(4qb#-p^8)_OHvw8Z7E2W!GZB4g(2N`reu%k6%+5>_|z@*&PIf~`K&j$W4F3wP@U{txtC@zyEzZ;5P#Q$k(41qMxPpZog&H`)+(jJE4ZSYV<u)7M{II{K)SCi#jrcsBda1GYPPbj>Eu438VLMXrt<-#Ifzw8Z!aH#m*0!NhzW{v<Z6m%fg<@O3ok>vVM=Q(wpDGcjMstnqb>P+D+ig==i%T@Tn_kd_-|HE*<aT7f=Lmv9DrAiKc_Qq7zXbooiqcj2z}Cykb-QPy2?f<o!8ab(sB;>(;Md*K9$87D|oC+IA36pB>c`ZNAqzM^?*S4X|o)tw(cRPruBzv6@DEbpb*xVOnMa;>hX5Rf1ShQ;Eq*;*H6mpC^UU%;*TmRzmgH5YAjPAogn>&sAAhx!<xaXQ5%#C+_XGIwBTQ8{50aEE!Xbdm2fI-+KYu$_O@+s{bz2}QLwc<CPFp4WppVlJ4&n#){~XIh-@=3ON{5Y3UOhtu74xr<|&FkDI3FsB=1CF0|#;h)7I4&{oJg>yv;^l=`0PA2Y+nRRar;@;?M4$T!0#z(1^WP;R%2P0=Z7+F1-qKl1ux5a*8oFto%)sQqBvlLBV$0P+8T1j7qeQjS9`0;vt8XuGVa(RTpTpWhCl&N$Uo=MUAj7*w^CSLKi5ft?pIFPIT4uvE>(z8@tFFUy}@~j>m8M~qI#1r8Qvt%(dxxq^ZE659W<rwSB)s|IQ%_k8d2T83w99*l~vQg!U9bUH9B4KWXd=gu(%l*||=7colMMxx0!ci~6xK(kI#<p(1QBFFcjc>gHw_wei_JF{&R7$&!uXW->Fb?_<(ya3#xSjJMn1y`^<ys>twQa0ojTZKrM`5`$)^H&k*}9zbX(FzcrHR_(+(-XHMgGOJ3;#k@|DtIB!fU}+|ALDI2cvb*nQni$cA`Dhn`>vnX-uYh+TNhwYMJ2DTCUc(Da-1H#fk%@O{@GsPn>p90DsI=sqx^a7VMc2s)qGdveq`nHNJ*!yPtrqmWvfh3GU_-Bhzy>Ppguc<N*J1>5PbRYg`aifjwQ(46p67df17N*^E`c4b#FgZj4x;uWh{})jwyc8g3j<iiQQ{;o_ofct!Dfv*f8QQ%Dhd$i`B~MVCi>WS{@NmZA;-Tvp@Xq=lk1rsjC>!IEW(e*~)=6K#*xS?!jCIgsi}yfwv1s7D8qK@Ma$M+68%q5h-4=L-K3D=BKXp36j(23$s_;PN7&C|yR5xQy3)L_6ygGHVw(h2k>kq-UH$U7f;`okH#i(`L5okzl6v)mTUVu%*MzbfF=u8pWk+_)3pNU3F7o<KMW>L-iYEYq^_6frLdSa;&dpmhW-S7i-S>V+_e!x?VTXt!&JYz+<}6+6uE^!&z3kGK47f_8gb5J1{=tX*pxouWx}1+bn|FUHGv6uVdYb6|;{XU+LNxV6jg*WSe~@iB^qWT1zLE*U0}PJ}vde26G4Wlh`O-Y@F({?nc7#Bn`R)40Q+8s<NBbZ))wDlA`sawRBhm(^L#_4jMR~#MU_nmnF>0%Z_a$t@-$0*Gg`TV5YhFuX)$u@~O?mlP)`#%#7<`s_Rg+>)?a6o8w8Fc9zvX26EDKm*FUFH#sVzZ?qAuD)|tzS>iD)itb1@26f!F!=CKV`o=2B1vhR%;iy<q4#CFtnI<V#vpR^F;te5T9=)jdiHB(tV^<dMB3*h*ONEw4iexkV_>u^;a%Oe+ken}CzFLaq`cf<=q*kpG$RuwtPMuvmm~Dwe)jB~&HH~$$(N1qODNXkcg%Ry7j23)>HPCCqqI{nk?PV|z@Bf${9P7vBM~Vl;t20mH{o>N&xeW3My{4KP_39*1kO%G?V;l+W@RflbHXGOxNXwXSxV`4E`B!<~OH*oDfQMgrX?Dg-v(-y0*-K+7&0!0?G}s)<-X1ngNy)6+-iOn4o|@L};iGlcTAzk*>xy0!|4xaktnmjF+RSsAf01kUW@nex2TeD?Wt~OKdT++2;&ClolV&*0)uJZ$#aqAdMMKg#)~NO<AjI}+9g^by)ye26uE!%1CcMqbK8a1lWfkyc`3?g&W(K!(H+T*3s_GppdHYDXZXbVpx{?Ojrn`S@&u^nNuw`op?$~T)^$wG>)jLRoQ<y4JS2Hsc@tOVE>P6c)yDZ*uGuybU+j!CKO=?S;2DYxU3tVue+k=W!R%~d|5TY}jTJrX!$pqW2-znZ*Hq^LqH6-O76SiHoSg_qKN=As0RAVfcT*#zyQChO4PJu0ngs?T|=dlJF-7egd=vBNlrR=gP7EINz49#CQrCi@DB5Dk@U1TCQZHa{=^DDFVvu8VmQH)>N8Tfpo$g&gNWyYS(k<zltN?Z0`U{zVHw5;1ttTC;(W`vSE5jV^PyF_9kVzAAO)l4Fxk5cvLR@E588z)U#m+j^D@kpgHdi{DSb1gGV8L-6q#sz%4yQGHQp=4Icg->-n6=`u<k<r;tmak)W9c@f{*Dcm5#l&h7m*r%#e7TPU0@CQ~4dBbzh2~p^_r$=ARUrD3sjfHQDAQU%<l5Q!OHZpK(imL{XTk1VxGeHAE*^VZT&{|lyGC%XY@=ms<Cwr0NCGJib>|8VGmzLVOs;yKfkYuKy0QuWbFICmv05@`)bNM-{#_}T`DHd>a-F4etz52UJ7!)dOYPvD#P+F)-_V}iMRk(nmf`FUjRZ5f){BLX`OHT)1-qPxVe}~sOC&g(3eLCht|QmI1bh)+nHnC8*_Q+3(o?g`#y3P+XqM_<&Z){GM^vgc47S*`hHK{}Yu578>1NS`e#G%n4ThAG7@6o>^M*PuAxEsUQHV%fI4%ZsTqHsg>t@14VjTy4!?luDoA#{Pam&Mdyt7<1jkVIX@2lcaQbAa_4gjJsn+p|bwxz*Cw<iQATIWh~?X(uxoE9c^qm672=|06ZU&ATQGS)QfE`63c?pRjIV+-d^6We_jeU*Nmf^`IJXw2li$VJo@BT0u?pB$c>RI`=uYU<OBtYzA58|t!&kxQygAIAF{CSvAX74-E!?si;kEKz9sJ|$1yE!v|X-&Tl>a@4I2H}bCF=30ei+?TZ2E4OP#>^QO12X-4rX)UQ}c5702Mr`uNSf>`A|Hrk;q1lp#-(_TqBUSAq{|s|xY@%sKk|Tk-V<C<0rK8mKC0%-B&5Cv!fhX;pT1R86FKaw7dKMWLf+%nv5S+C$awW%`+7>_({PI87d@*5c@SiKAfaEd)IC<%e&2iYWN@82IGiDiGm51(1=-M4Yv^wO3-q26r`m#x@t!=kC%T|UV<ZR#q+sqb?n$)ZKt+ZWJn4#Ue2oy^R+!@tePunai*he}r<r<)dEyn1zjXi2T!48R=w5(QWu1IFutBTLT3Aj^jM4fucoC*@B+O;K<t5{Px*2|!yA8-#{QTXzR^18|wxvlbLz6est^_4Gk45_SAq!ztD`ljurv5M7HV3&p=k?S#yw+iipn@=Y+RAzCE_i}qNG>kG-os`61UF7)Kugcd@8mWJLjA3+d9=a<8RG62v0{&EV$zud<3T9<(<f<}y75-q;LQME$p&bG~WC_Y0g2Ow6h<>hY7}M=;jskNT!?w8GKjs)PS*5@%o3cQ!-axKa8>Y3-;YWjz&UiV~pBv`PJ8qb#3|wGF<uVGo$2Oy8BQHT8eP^yQLR!6aI@&UVJaN$j-u>MsFa$M&t&vQ&=MATH!d88)Jz?zGSFSzVXi1j2A4h$vm_d9=<{4b5?aLI6Fs9wnwOFPD>)FRmVzwP>T{j!U{EO(#SCJ?T&Xty%8VPx?+(NYK=$uL-as+U47vb>UUZQSKK;X!A==bQr@!?>lA{=7I$B5{41mH?&E||5lQN|gRv57I|ByYHNR;dQ^eHhXgBJ|3x|4k8Q?PTzC&Hb5(&ou|?Wle<Qa!@RrV|!$k?y+nRaAxTu%&aFsYTDP#uuVhcMSnz`W1prVgxWZ9(k-HEQe$6%N*Tq<dxmr)+b`i1*C`VoVh2h`yiMA!rAb;|*0{js-M+1%<6zdh);$3jQ%&PUW0vqFE$hu0*(t|j14ly?b<MFBy$|X6hpcWEuv;u_nHl3i8yjzh9NIXnkaCd=y-49kdIN64Ikt~;2U{bDdMyFZWM>U8bH<mgtV*o#TJTZ!W>qt5tN+qiYXlcg3XMi=E<{-8+)TX|O~W(EH_blN%C`R3<9}UiteA?=1#OxQJd<pWXp&W?$+E*XYvTS(ccf_uoo^!DQ*tN)nv4KjTmaagt99#7iH4i>sqxcrwn^EDX1BZR=30i48NPLHtr)1F7EX~_Ia&7qZ|_@sB+0ES|4N~O{WhxQ<>k}De$WcDYhxjgps``>3Pz(fQ)3m})7{(EGq!Bie_t{fj3gsS#w8=FlwN1|Ag8)2vXYG8<M7^d&#7*eNDGe19rv<&B1n+<Y^3BxF4PzNcc+bfH2gt;_=i+1E1w$VpS<Xok2z7?0a=HDDVib8Y~Zt%3v)Nb)K#haWi0c@CisEKr3tL+X3}j>6w9jVSk_TuLW@X>B&|3CC;2SmwxiqLfB((O#$^7tSxi^zQLtR$a+Up4DV`M2QT9?#0IDuLsU~$Ew<}4(-0`Z4C*8rB2@8fHcSnd)wJzuip2SYwayC@+V%=)sr38J9Tms+4lK_fq%fkEGikKW|SwNAc0b7!oaMQ%RZcR*mL=&?=p)u&9!Dp~SRVFS<LW7)lEo5jUsIxSIRnrG=XN&PW3?;L|XaNDW=E@@<qw~*7(A*k_5IMyq?Ju9jsoQZa$XlrH(pVDzW~_u2f_9uW(rrlwjTxC6bI6OKgNbg-I?Z54JQGzu8_8o6NWGk+beI{;X+$QI>w9vU`^|u^3yb7}pE?&7;i<n06nRQuI+eJ&egUQufy)|1QnomScWQJ4j3|EY>2oX0{_dpb1T8(sQ>kufiG0FM<@36M2|I<Kv>(VS)?H2lY;8@?k$le)Skk|K<1@MTw79QW8Xc!ws(EFeBF}SuFBN`JOCO?lsvV5UF?LD;E7>AsZHY>jBnNT=Q;vakR5R_)3rqkLr}2j3ZjUrvE)y-<G&#oVF^o*zby|XIbuE@I?|N2UOVy*JR1B(2S?!zk?fuP^SFI9sXXkInAT-T&)s6YfPS0B!uKcFqdgZbk2U1$Ky7}#eqFXx(24nU-l$%Neo^c1H)4lCl0D+q^Jqd;+$?QfDJF60nD=T#CuO5+jvut7rx#O~rZB{c^X-h3#-g4O`U=#?5nx$TIr`pFUkPDc=LP{~}#dBJ<r@@EjhzB{7Xo#^6Xe%Y~w40<!E@6e-BTeX+Ryh@Y!D9MEF)HN3`<KysCeoaEBI7?=_g(+(M4o!gJ<a${$8nDkmzyep<GE@qtV+;QDz++<ny?()X_TRLaj~~ik1|BU>~B$`zY^W)R{LmXp|DblrnF4|+k<>7Z4l9}MMG=))joJjE|%ZqVy_zm`b6tr3<Dn6(t9@B;F2qu2F5MLYhBXhV#T7?aHvwdUI9*H{OS~&PV2ZGB9~}htJ)(2%6c22BS59?5n^=+%UdI)I|wj&D2lVbD%mA%jEOMwa-y$tXx@Z~#W;DtAQdacpzp2;5na0Lq3kQDkM==q6p8Pv{F8!*v-+LeV?9ZPnX`tSE{Xn=fh?_bp<XXIk98d#9+$fw5uvhGM3~F*rj>Ky;GIIkq8zWPKtfdy>#;se=$^Vn4sHxsm`u6Km{4nL+<6yJD-fzwpNCMEuhE@RKheziVa2*h1~awgbq^CJm-^Rs1`v&<VZtmf*plPrH#y$xR=7E0Apl482KX#xxsf8HtHg%iAha^*BY^{XK_kPK<z~D@L1F%qc2Y?;urJZ`12og%W~0^=P@{X=#D^W;+mb`0nmU$NgSFI#scryHtEz{d9Xg`#sOQS7`BkzH1I2HmbBZxJ9jW$;Jo`PiqD(K>gUTF%+U^=>++mM0#3kwREVdX-JeN$)PS#uAIV4w$J4s!c=c|ITTZ}=L#XWWe#VHAHL*f;vI0a-pBSm<QA_^PUeH(Zt6fD=i4VV(xZIQrkD@wsw2a4E7VYfm_<$ckFFOd>e3Ojel9l^CQ4p0_V4z(`gMAge+Z+bze0#$i%(<;N4*WGlngU8HXUUy^=83`t;l)=thLc#nd6nx!8F^=a~M3T<ha}k~fg{V0bFOj&xCZwpfO^_52v4b5Yn#Gg*1&bkoT8M^`iQ?62u4WQ$f74(kS${HvTYyyFZgPhsx7JpsmM_kr!K4O?BPNoethR8LAa`_j=5VmzZ9rTaK9DS?r7C;4Y~6gr{&4isvJui+Kue&CF4JCE8J=)`G5V-spiI^ocy5*eVvql3dhN}-{5Dk{FtXJ+8Dtlh;$&s`qdWB=1|&RrUyN*fdDCT+79mTKPfG%t-z1=~J3zLBd+Onq+Vs!$d$Y;UlDS{>NnxGbSJs&NVenigLil%KhRmaEGrx<|yE6#h<VCR3^v+vTZEoxMLYl!@h`S}i%WopQS3QFd72m3%(iRr#I$N>r22L5Q2oNgRr)Xi7!^s4dG08iSonnK>5(u*FF%ZSik_*c{L{yjVsIomp$Mrf#o~e?q${fM&mpQ6lFxMwaYOF}DuWF*Cnd_C%g~eXrDU}YUwcJ;<z03}LYvVPE1C<Uf$x(ij9KG&Pl@;Uby&YQaQ5)crvfTH%XE!VD&f}iRF1M=Z9p%J|FBGuz6g|uPjF`*dY3!bIQJu8C0Wd*h_Qb?gqX@5XvjN1}*&n){N>EKG$tD~VijOh^f?CItgRr(-0addiW-xV(;}~&~tFLYLnV9Fa&ZO>DY2ZePqWBVaN|4L0(2W6+{a4FeS;dq8N`~W8QD#Ykyi?SGt7i13LUA&{cXbVXK)5YtfHW!-reX%XrP|4Fs-4%Z+G*^F*7&%}_p5Mzi&~jMjD~~oqJ<nN>=xD)#5X4f*ZbMmGS`~{G3b`;LD^)#E+mtNsa`e`okq4g<5KPf_T?EC!x@YOE-eSz>eE!yUExLn<J^v@X$TfvL>05{mkAiiQq=`tYk64;$fO}zq)LgEZXaOCkusrN->ZeE<Hqqk!`ZNiSk}qcxhAB^$=52?QxMpp30bFJE8a(_K`9)7)XXZa1+T#p?x(1b-qzf*6lq*wi7e|a2=*$@DEp{n50el}?nD-hXemGPoATpzV-kCcz><7<12~_9pQ$!XyF;|qW%favKw?b@L3`4q;FQW3><QZriY$Sdo!}UFy;(~D0;IDfXSm`(R_V$6wMilSthLlePsPYxh?B&%)?H=wctjR@9!hk38E(4dhN9DYq+J+3#NopG5yk2Tu%uIcLUhHtGq@IRYt)CRDLV@MdkGG}4!YC=&uv{HAd`Qb7Qr-9B2(+~VqOGgZ=^)NfIz_ZvMnSLWk`a(G?zBdr9yO(R;2%_J(BO{@)lSzk`_S8s4guvNPbg;yl$|<*p<1}9*xax4{(xl?gYlVR!{aqddIrwID3f{sMAYcNDU-Zgwf=GRM*Ytxkxdfd?_SQ)JzY9kx4FmRrszVWieZGO!RXICzrxH4)e>4eH!DZ`Je#g5@tfZl8QOJTHp|SC@U%-veCZJjif4|$}}^lg?bG(((pwAL9kAu3F<!IkF`=!8Gs0u{-=6UPrWgoAwBKga{62kT<@fyGz~$e;T~+MY~oF2^Sa5x>Hznop5=~hot9EgEi@(zHetVos#jvRlsI@sYM^Zvd^wbk)l}E@k4=x#6R4PIvF7FUW{z@qgy;cFa*Tx2tOX|QdU{=zEu-~Vbc}Nor?&NBrZzauu&iV_tCuMYMpvBQ8<Nr3MZC~x43kzf5Y|hRS9ZVYhuUk7BR43E+A_Ah``ONLf>J|zgN6y<sKGUnakdvuKsPhoVS#B5N?5U@Eh8+ga>l0d1Z?RI;!SVxx_3iqUdLVH6g|P>@y=KXGI_qtpFu0rT{ziEn(|+lHW)>6qm=azXFIMqS4<$`Xa}l;F|ur$lInW^?3h$|bwlh^Fj1olCc$bP4G3j5<*2M^?zKxC!^GTD6xt9B&J+Ib>{PG2Mwog9>)ZkPost-OO`3gYm^EcJ$<D%Y>{JP?he~@&R9u*a73ox5Bo)9%h-=3b5ct7xUeXeq=azyK-}H_7iM!3DiV!pP!D-jY5Mo+Y39P6p1FRe$LEgZKtP3M*WjV6twZ?+UuPTvqxh(4ss!nn)+9pO6H5QB~=Ulitdnu=c`2!Z){1{9Xz+1X9DQ6d3@`HGjAG~UasJ!*wD>|dfv5oP7%3;_EJBScqNQ!ti%5NPKP&UB_tHTBhLG)Ok^GIi8(32@pz+aF@vs+2a178T4wL*ZzllVdlfZ#*<895t$Ze?&NhY?y4%?r>*Y|`l%u?kbax}j$(anl-+DWs&7)=Ay1u%TmlL+7@klhQ?NwQdtc$pN_1id8K{El6Rxm2Ur2LYt!1xvkJz#i>GZm7tGyKtKJvS8bbLjcu#*^p-Y7RniT;B@~A@p}6bzm>4O+DJ6TWvGb-{6_p)Vk2YuGOsiP)o;nNkIurJ+H>|k8OqXp}ln!Z@<rZFrHVbrXvtUbI32*93*G)MaR9E8F`J1UL@&CB$N{l{*^WX3noxZGp`nIH%@FuNv-N$!vzAEfa%#jWGe@inlx`1hJ3@SJaPQ<bglD$q08{=3Nix4{XY!U;UjUW(ZnB|kh$q?aDhT>zUr1UX^Bh<K(@22Q-*&Zwik_y9(P{!+B!&$W#dF|$sW2&RgOg?HuZOG!*<*;=x;>50)^(GiS9JA(ST0<wRp|zu_O1ygYXRm~Fb9pOXO+%|T-R@e_Qh1Y=x^A?JFROxHak>twv<L`N0VlbQL9a0{A4*K(T*L-UT4ac4N&C%NKs&_Vwv+!h18oeTMM6wl5;+5NCel3TP8iA@F!Jpov`nsZ=ow~;iQQ6zMtXiOJ*2B#b%`t5E)VI^Y89LX!)g9ejk4$IrXot?9;9OYEKUFD&`EHhDFdxJ0>+GcPRc5Mma2QA;5IQ1S49X|6)wk2|B7QST#l*QB^Kd|4?%aq6|^q^R}5zo_~o?#S1JK{-s#)|O~3**#9|$==Ah96GJ(6I6PwFh;Wc80ou|$%*iyy9n=00IV-~4LLh_Y0H;Ck;(Z-_ELkCEJkX#kQ*8nLddKcW2D@Dhs?;v=WA(@q<MVY~vKr>*%9asrXv)$61F^a*|j;VBS5T^h%#hBv4ycdG7ZpU{h_^gV&qHRf&5=*natK*G1e6nX|Q}c`Kz>C497&SWhpcV4d(*I^91Q7#Ukqj)W!Vs8iRmof!LZuOUQG^gebqYhME|%W*_+N>5tjhokb&RrH$Jm+Fho)pUXBA-xZUul=LNjR$7kex{cMV?N1Lr7fW=Z{)iWS~etgaeEOpe#DQONO9yLiW`YhInX+iN*;F3yT?FJhM5jGYHDl)qcU9fDF!sk08M@dOy{J3+Gpj6yE6vKu{+tWmQwG(CW$$dCu0J28?-sBTMHM*nU+l@j^;BAM0>Uy1SJ3KO<<=5CTu677ii)U0p7P;==C-6xIm#TU3oscO_jn9EuPa*sI)mxpxCOIoccI%QF4mA<4hF_epC$=oKJR#S(?yo$~;*)9ZI7dS^%4Di@8>GC9jb1FLH`JbYaXgMJzpi^Z+H_=(e(L_lj@$#Z~#m?84H#J6Sh9?42bk>sX!kcW@m7_ELVl0e77+3H};Tnv0rV<Vl@QJiN8m|xGdK4g-&_4KinhURpo4imj<FvwgkD}KC88wVrZw06zEa%#?w2p!9%o^hrGgdefe_HES!~ofW8p`UOCRKE*Tus!dO8{dqS~r`BGUe_zC_Yl`iJ{t4x|^-!KF_E0(A@SGGJK(8RGbwplg}N+E>S*(y$ao_T(?CtO2~4UB$$;t6bw}<g+RJH41hao9z4rs7<47lD%f-8!0k4RD*Cf;*1Jj-{S|dq{7J1;LwgeX+rqkv2z%ylQ;f~YN^B0#6m1243L{BE{&z>Tm8LL{X?{<%B*(-}a_qWAR`g3tj&T@V<m$wwm#}~9w;AP{1QMbG0iqbX5nc`>EceP=Y;sZ&Fzv9f5<N}-Z^KR(ha+V}k)~9u7QtMk<`+p|Pnxd1aq)bMu6#14Y29S1?T#XsA=4|a?&Nf~xSX2O_Gru7BX3AdaMfqDVuX9k@>&az2*up)9$!mrU4y46Ob9WeFp;Q5OyUuzDohC3uP`B6B4pwwLU!FHDn6TeRSFZ8WPRAav;t{B@FOvq`k9+1bA%9ALo-Cc6~X<yCx-^Ihkp?psF>{%l^`5NE624!d-9wm4f=IX<gdh{?PGM+!*V>(XdT88?x>B`loE|?Qc#AXslwYlbS4*>H>hsxnR?W;T%;Sj%+#aGZY5JGRq5p0@Nt)2ycAnim%!{#X)}j%HMr=M6h%3-nG2x|GZL6W!|kq@J4e9;cYq8m2-_BykVH4NR8Um3)S|>qE$X_(C6qaTFW+MxaueJDT3%1p%r431W0c<)TsR9A5XXvdL{=X_a3C*+Z<*w?=UOParI;v)?yL*aPN$@eCT0Od%;Srw*Ce<Z5^RF`2|3)L844r1#?DKbr3@2SWtAF5ufv{+Cp+ZV?!sGB>fbJn*W@vBx4cwALZ(PHtwSkDU}{%{+?I)}AnOo;b)Eh#qV?*&!a)lwuy*>lOe%Ns*BYe}wrs%xC%M13sjC&l;LZ+vAYrG*MGQE<i<an=xQR~vhf<Nb9CbQXr)=O@`pMyzIC;8CL~V7!|4&3~{xj)L3DMw8iCZQAb*~uWNK{Y_F`z&yKBfSm1F1xS0cnLfESu9T;3klK7qjCoQ##%V@}=p<c(ooadkWg~Xp96<P1~Kl`n2AH#GQvg^MjB*H+2aBvYxXYU;bYYi{(OUA`gqH)NxLhU3XY-rB;{YT;{l=GZEPAGS8#pi$71P*xOW!y;UdLZEjm&EAg?ac1{`kCfEAc_MQeb#~rTHZLOupCT_*v*G&ah{6)951}k@V{7?=&1JjZpUqw5zYxU)v6d(ek|2d29^I#6dQDnGRTD!d*jIb|Y{63v-V`I5FZiq`tQgzg_>4}&L+)Olts(sFydpc5gHP`C84L}P4n!*9?$|`b}r<`!!TT#`|dztLpG-;EK$D}&Lx_IXEvfG8dRaf^`(<L=*lmM$GviXZ@C<!<UsdV_F7)nBWN)_}@olQkaMQ26OyGkm_l~XBndvn#;Uj;2%>Tlv!1%2ITM)Q(Y(5F=}YnbbV4RaGy!;nUcnyWqx6H1YmXVTHp#$-N&7b!7r8gJ0)C6OOUknSp$9pL;3+>zbwITXGpftgZvY@3s8Zhv$4g2~=}w8=kB$_QdvDJV6>+&rU4XIJ$KTIwuTeoOl@l}gAv5?nD=W$h>@JJ5Z&ajO}_7R{{aB6(V=9ouz~$({kMY$kauku%j|W|6DanY@@;rR6N57{HL_07jkDqx#BOREP(bp@^A=Z~;$MDpzDDp28-c!dl(3hMCGfz3$d6uP<-nDVlb?TZs}p)l#Mtx4Px)4py9F4~%0l35=QfDd5hZ#;TFc3Ij~?B3ni=IIGMOpNYJn6ZLXvRkfUC=DDoS!oDiZqpP~;=bQ<$sGn*$s(iP(kPY$93^zauqS0bkSYpxk@PxxMZn@-&3keh-LlO{}PXwsj_28#hUKhhs^RY)uw<;KUn)s7y%2_woHd-=@m@$G%pvuIEVclU@WU_s@a@h53s0)@V);>wzDGZY`tO!_&WeRpxRJ954&`X0mtqORv^eM%58Dav7Ml7#;vVBSb<8pc30a%un4Z_r}K&)i@zD;RS@>Uvr-E?Ws6nJ4bzMdi)lB3@~9hj74(WHeFdXnagH~Hw<n}vgrRaT<_%W3cdhisDI{#XPgOLQ#3pnh2#QaeERxaY>|FEIKqQ|+vYw=Iqv%Z4yz6-`(gL1cbv#->Km(^HRS<3?6D{7eaMT1cvV=SqsI96hmT(VbHgv#d(NZLZpG_`>#>?=E9}E7U7T#Qxn0(x!iRc6?O%UwMueT$ZD<tu6mn?R?#8Al?z|s<hzh8<aLv$um_Et|(5XLp=#7w7|8d=$Mj@rCdZ_osmN|&`M4+UfU#Gzr)Ttb|Ig0eJwjmlmr=sWZgl-Au>AxGe{&6O(Mxhe|U>ysW3TN`dQ_$B{EJL3cLq)h{g0i?xUziTI$er5Uw>sx^~*3Iw~}C9Th77>==#+&4JO!D$EL1+Omr}qYfZ^oJ+}?<!C#@mv@(E*3S}g!NAvxuywgL#IR3vY0y!D5m*%kW{Pmr-jbof)S%K9QJ~TNRc~Dul}7u}yI@)?Wi6|T!WrREF9Rz;3oUg~5*W&s%ba(XuK=`wps5%(oD2Mr)0n?$37ljt;CCyHzw&|>@v1U6V<N!ru;aD;4|?{&y_tPigmSyFBnhes*=>s?bpKoIAY&+Koi6Hiv}i>=XIE+;Sxyd3uX`vhdC0n|g?KJpTJ@wlCG18*97<1e%5E3oQW}cj0<cae09wLlz>6Bxpb9S!X>w%NI;6QPAzf3d2<kx5ii#lVM-q`fViPL`QyxNgND-Kh`@RHCZO)+MqAD>c*_-u>zP2V<<aTsXfY)>~mP8jV+`%h>$xDqE&Xt=S@ueh5R0+AMPN3CR7d%INw+XW(QA{ueS<nJmH=Tj223dQ2r8;@DHsdqxu{^7uR#+CzR#a!<e_wg!hPzijS5+B-7q&n-pWc~HZ)Vd^nd;liTT_~rN>3;LN_gzsl&UCiasgL8@j>87CVkArq$i~wW*rI?94u1KK|L6}U7y)Q5Kkk8qn-&obXFQLf=L*!RmCvDrPaW-1tCs?ql@D^jyhh@syS#n;U%$v`TruO5MnujcfP4@QJM19G!fEeJe8;6SlXsI_L{!4J{tYnignnrwQLDyI#FqpSzpn-!d=a)HW1}B?z~C&BW&$Qw>tmpW_C$=@_saH`!!WA&ljYWJ+4DL!IX~LfD!3~PGRVJmXmkc#iG!I(GBHAxI6sPO&1p~A_O@am6LsZ?Q+VOki4T+en!_!8nsI2c3~p!r*2wSx6w@EO~^H&il_DwWdX@bIT~xE(s*AgjY~gVtYX@Tx}r{I6<!pOti*RfcW$Ms$*8JWpX18=T%GBCu4o58NF}GGXzjGOqW|mOY57$Us<yeGBg`vaWnLXR|9~M=Aj<dwL&2A4#<)`+BjuDB$$2R1ow4}EsOdDa3dCs*1E6Wj(b76{xE!4(mQAAjh?&8o_1axpjq+b0-~p|rHX5aPIj_=cDvfj(+5Ksxsb#{5M3A~CUD&P-=(DLED2!NmTqH~z2~zesvsH5|Y!x(R8iazc`A2Dp-0~u5f^HUiXPDd?KxQ0x;0|lcYM7h}rMa=%p)0P+^rMOlVXt~Fv~>t!jDIBe2uCz84xTFLO4$NNx9a`t21bA{SiOHP-cdnu&nSt)7*HePy*Rmm(2LjT+@W}+hOwxzW;yYh$OwWShQ&f+7?dfh>Lm2=V*@@=QaOOY6vb4Gbs3%jGpE*Rf$0lx*~oOVW>2}Xqi(HFLa~uFnN=$z<xUJl2)z?(kO}RO?xJNl;t1t-R5g0yb}bAgLcmP$9!Ik1L}p@HUW^$*J@t~wL{1BCwFu8Zu?VkBzgA}z;pyl$60Aq6b@x2Kt|)9&_732-7yh)%@M`pH(A?c%Z4np>u~&wtI8(+dIls-cv5}%>XLwq8FI9slq;7@xSMF0LUr;G>H!2>u#BMorv)NiAzS7-CNs_l2CptsN)segfv-7m|qWF)E!3;{xUkQpC6`&Yb%rhiA?<cKPo{^lvFByK>6CVrwb)wgK9dF}AtfkWYi#2j~4&-dvxd(-FvLss<J{$I<2;^rj(P3XvO%i4aCe;DXBcdSGftI8_%xp`mtUDW(`Q6!CO<Docv88)*Y9L;MbJWm(%~qjY(K`wxEr!T$U9Vy_^=7>Rq*x8o{GKjjwQ{Hm8ek2&@_WjmuY{^uGl<(>wzZUH70m?IshQB0p#(WtE9cf<qdcjOgGTGS(6o`IvA9J><JK*Bb`wdsa$O`g!k($H62m+}w@63@+zcVMYU%noV%r9>NX5?FkXA}qs1GmaEum>hCsG(MDn%!>se`l$b3zcg+doOV(=-Cm!r4?W!ouw->R+sYMH-<xqLN92k=j-SK#wO|Y0_5$6Ah&^v&BsyzS}H0KNuBNJtgn0*xV<)6$h5o6U9$xWl)2n_yX`QV=~oq^&-@7BC*-jbBX%RdJD*cX)*<9vIx-18kS%h(KOi=P0LDY1l9oBs_3Q^O;cqp1MDR;L(_L9{b|}lAv7u@xa&Vx2zv~y?d45PD_W)zGqQ6_#!}s+4X!-XC|}igW#71Ba}ah@+4f|(%FY)m{0aj?S<NYW*F@dKSW=I+S7eHd{WwsGi357x`Lr>B7R5*msIHTA2wKIk$tX{WR&zzG*I!eH(!%jb4pMwn_#m`YGho6R*6lrd4A)gk1h|+Sww15r68w;AL^>0)Q@}~u6<L1K^l5BI$c*s|i80?-k0Irvn~=wlY^t`TiuM0KDO*4&b+IMerM09v6UZiaN9CrquHqB-v&*GLd?L!(KI|qt@sVubuCDfuQwhy195b#{OI1_d>i(}=T*;61*U0A$6==~c*?P5ZX2lk_&nY=^69*eUn|KtsR|6@-f~+0NbH$Z)hoOVUlsQD%el}1E(_qapR9fC}MR<_$ITApWrlo9osbs3hmsQJ3hVPhpPG&9U_c-2D0p_->i~oFWpUz|vr^R9I6p<P|6iT8+Z%MT6O7v`OA<Da4)okLTNK(%8aOhL-034wtE3iJ$6kqq;#w16>?B#XG8lA|=fn*O?ErCQOZhQDuYxjur>$rAmaA8u|-BGA*XXkC78)h*>!Dm)VO!1#35+a}Jl`fom<}UU?>CgjrbVSaq8QKU}fQBOaK?5Q)IY64Ot78aXkKGbJ2Uxs!9hXw5&h2xb+yUK$Fr*}&#vSnXkl^CC5zDiyLVGF`+B3P%9#5-^pje8{S?B)Eb)TCRX8+Y#wSr~;l?t&{xe(iQ?%!i2Mfsmy{VmA;@OB+G&C3eXB!GfOxsj5$?fa?~xcq=PQ}LuB0!6Pkh51wt$k0eqKGeKe-SI9{!G<avt_2uCrH)w(7R)8hfq=tYlkVDxR-!ylm;X5{K9yvNu8M5QoOe}58G%NROIT;_p7en*S9@7dQlhZ>B&vs+Z%~7Ix~U+0-U}BLB*>x(m7CAi-8mD*%t($=jz47x7B-|_#WCK;qco8Ht!&TI)|{O#(wJp!Ons&fZbflyrQ5j|5#L_kVoK7^)~QB{YN=zYn>yx|8+i}$Dfc9udUCR1R7$47owk)4s!g2PX5&@DCtK<)C5?mCD3VWGg|YsSC?q9)PGg_ViA<aL$dCf?a)5Kj?jfc=gm8x;K{>b!QpndV3`;SF$-vAh8IbM>PEmg|Jr$#{lte_C4UjJ=wzef0<51MgqCnl_d<L}H5CvxVP?bx!`7FuU+s4YVCEd@uN{XT>fLlSUXo$aAFSRx6ZCR`<5$0vBx2r|J8&B?SdZAMDi=6<-Hp3G&%~k83mO!D6FBj2!(TS|01b3{q87(})Q-N^R5@c03LDuVrKx0<houZ=07VCypG)%0l?UGGqKl15JssWAFno(VekbKrG#e?Z#nmM#!By)X4V-7cOU1FU0y9hXsLU)pnx*@^3Sc1JO8Sdd5hSQ-yj!Fukh<lKnK_ksyEXLnzN5!w#;cUDns6MI0#C&lF64X9_B~L5+<q;RM^MhCeuDOM@&GMiK?BNPcG}t2)tZ5IDY!`M&Ocu$=BdVLBt4zBWS7zuY^<|R9fRrrrJwz3PnJ!-@<yLLrC}jAeTG(6lLrGLvbQzJ!Q<ZxwhAn(A3MKZ0R*0^bGKF0&bzXH-=e=&&rQqseR~KBOM@2AT8tXN?1z2&?iPq4?=n5)%3@1|G4m25)qSLuABx1L6D<7m#5(PZ6>RnnHwMo@;2O>~B(1W;9z&N)Q4khbR<G=_tBGZ*Kbr9aZ!1IA1-6pKVgO*7=bQcP^Q?UbDI6Byr?@Wm-I83k7N|Sc2aa6B<84wPvW2==~B*+-vQc%TKnZ)n3o~PI<<<iPx&5Jah$v)G`rFHv(bs(9$2_|&SUtCF0Mxu3#gb|gJmok?YdxKrjO!uY5wi$Hd`CqvUwer6^B{7DEyf6!Rwd8-*P5$?~k(aiwQxa1qgaS+f9V4Z*%<#^Q2B@XLB%Kn&dI}6`_IEpx2%2uYAUPC^dAqQ2y*B+`0&ql*d8M^_C{9!alN%+8o?}3e8Fp<1$@L+AO-W>U22vQ4yZi`girD~7ed60N4!tSJUO^VwrK8;---SQipi&OA5y;De#z|k05a`jQxlYe!grP~SO2TAV&W?-oc!h|yZ51SCLcr6~n}VcNx<nQ|7=`XM1~*;8B`R}-k~L#+nL9I;oWa3VgiGYP!X>tXlB&`w<ql<>DBg}vaiHnUVHTZg$pGt{4DgjF1#!IQ2+SBXG8}@KoMlW(b6}Sa5hh|%uvZ+f8WN!v-PjUewL@%$X0=N@1gB9dnTxWze)scL+ybit%a<FWh2V;C<AA30iz`hxEndm5smN*%o2{?c1jUUQ7-TJ};6se)7`#wo$bgdv1I|+MU-Q`z<a}0TPVjQJs7Q+r(InoYtghzN5F+i+L)46m(L5OuSk!3YEQ(&6suhD$Z`KQY6@iHo0z>F@V(3I*E7!{k0>fyEIbUAN0digrR7vPH!ftA_q$IB#OL~P1H)+s1#H99|7}9Iqp-u1jWE&baU1nw9Ev;XD)B3$~45nW<LrB!5?{(~)WjwYall?+oQV>gZIUf^HSB2M+>4#FtONz89E<Th|4w%CbFeIZ18k@hsjalM8@<1Slg`^Tn?Up>F?7(h*&@nXY8PP2=YDSM5DFg?qC<m-4xis3SjzO8o;WK=&g%FbR5zg`>3DAQXTn>rv6v;!(RLl1>*&pbj5k#-g<us&X_TE(0b(DUyUcXZnyp(OF%7k~-Ym{y~=~fK6y}Z_<UCc8xme&&hokO`kU$EDScI{^Y_wbaY`Jszc3Qx7fc=b(;_qy?v7gqX<SzFa5a(igXA!2LYZ$JT-pBuOsu%gPsUkUN1Kj<Ks^$e_8CBRrpi9d}C!)N#sWlZfMPE6H*{*?GrbyFfiNuE@wznHg$>ZSO^{1HS214=Pqqv9hZ4i$hf1_gg9i>?Djw`~gdewZxs1@%~fcn-kslrd(?9=u0=dP!8`pe9zIr*3JrKpA}6dP0<<C&;XO#6u!Pj4KUJ3jSq?m<c6g>ODR^hXf*eFj#<y<!Bt%qj6md5mGU$FE6Tw5K9SAeHJ8aQt(q(`5tBD9XJRhaImF}tZ&N5*9`{&UelWa#>%)xiN(Z#Lkb>f4g{v1388_gz@gb=J#Y9?tb=U7<d{w)i0#;z9m?26UYi^g%)tIkB9~pk7_oRfKx+El5A;#ZJ_-!n{-U)y*I%O}`)X$Xi**MM#z_Qs?2y=Q54^Gpr94KmFX(*B=RzTE2UZK`R<4y)Qc6B_-Vr(@Q{bV+s8kY(qPHA-DG!O`+ieF`%$A8}Py0rS*;3I>uW>=<ur-P(yF@pob~l(Sfl9k$2&;0~gfFx)MzZM*MGjl4b&*22UR|$}OlJb&DzcksxOFFD?#>5-ONqPYTgosafvNDuJ%mRi`ioTDOSg2h^-VYXy1g$fKLg=Gf1RY~vJsr@>pKCjCN!!p8GG`DBW_r5@4Z3GY%X$TrMm_GtiIzUNlWN%9X_=gLLo+=KIGf5-dE<k9Jkx(zNueYQln2@bzEPnn@$+RL>3O56jX?@6?|0d@TkX0O)VZ*c92Vmv*V@F#<~qy4;L0dNQ^VoTyo0@Ac+Xz<#SK+bxCzEj`A^TYpb%SIuj+Imfe(nr4oRI#Y#wIok6WMc}GZlDz@UrmjM#)yOUN*A-h#3cHF;eF)p(QiFWM2M8C>}ZfTF}oA&sXt4y%hfk5SoBoPSxQZplzRNWwG$mp3*h{YWT1V^q3cthHbV87xWLZbwWjFLiz&9DjiZAQ$-8i8A-52>cE@r`)yDASBYZ?))@+Sj4#_xg49D!qs5Pn7PQZ4~3D8Gpt5G#LI9A|&;V<r+YVLr!&R>r;c6=o)ttoGoi82Z?y)fT+WJ8c8`-+a*0l5G-ksS#^!Q*e>@Wb1XSuiF@(*4BS#)#b5Adz2;Xb{=68Vl12Pw&!YHW*!>)3m35Yt0dUa)zXY7hI;*A_K`2aKc7-UkVV4)VV-8Q__luO@uUp#l`lda9<$N^ts{H<4MW&Ebv2Ke*E|vL<<z?)Aq~?ZC3h*bHr)T<!{ShO{jn|s(VAUXWKt+rhKt?4!s{=(D7)VsHCWBKmuq5!S8JUZI7C#P6kNp3dkOrFS#5<V9hhu_b$29r%F>EPWI93>7%7GDmC`($CJc%{E1aqSb-(mJhY*iVNAifC12{-l}8Zm-|@USbBj^YJv0B98?=@^nLMV(k%3Q<+r?Ne3YnJfIG%7G_K*=(Xi;lBYqSyyJXrtn`>kX7s?nKNj{_A1q*xcajLF45+Hcfcj~i=63}s=vOe`rqVbPcDBrOogiyO@xrXX22YLV-yo%8v6u`F)=crq-y(j^N%FU3myVxYh+jDH3iTf1LW*jK?q7}MurcDoC9uzbYw=Aq%@EYZy<*^Hj?P9K2iap#{3smcoM#^fYzQ#Y8WZe$)L(Y$I?9<PaI^m$&i;Y%yK0G^^hkit;~W}fw1K@0MgHajCy?QDuIX$T3jk%#jYl<#+D|oPN{Neih!`336@nrsJp0g!lGpA@>&Z;f)#G3SYC_O4rR0`@LZ}~H5BOuy}cd0S0QA3a&MO_{pm;xu|t)k!9|h5#g-d^zPS-xH(V6@b@IgJ1l`Q?kxDy=AT56-oJTvix9Qxw+r*526jO>>6k<$`F7!<rFv6`!guclxJ3mPdfC-Y&gXj{ekD-S}eVrcxbPysz6v3Gug|Vs*JyB_dR$|G><u#o#{G$jh8Y5{)RbWq*FYE>GwztFyyTso3Xe<)LYSwY05Vn_x5zlr}HJHb_gQ6-=qI1Ink;{|#Wcvl2*$!}4uVc{I6|F<T9Z=Ep|EuogLR%p@oBv<LW~Lm;>n>x!W+YEmB6;pek^Z*}&Rkd0|L`0!-mH$HWmuqZh6Vo_NPMI5GYSQZTGZB$BAfoj`w#=4yIhUp<p_hDTc65H88O<)oEw;Nr%xe~gf484JvSj>*%=7l)d3+tsfd7#NjJ6uH9QIxp)qXXm=?;GIBJiSK?JQ4Efk=YyHz;ngzf}Q9B|PuB;ch|7#wVHUISqnfC7G|#jSeIV`_ZmOWz{Z$rh<jr|#vVh?YEt>I-F=KIa1CFc2)SJxU#-tkh9rw7o#=s!sGP_aOCR7kbCPoG6p)PN)ewYFQPSn^nPeS9xyy%P)Hu!K*-1#U5A_$81-&I)f*ZzNdxc<GQ6@!0o6ELQDuG2!&D_u$s^p)3wjTAPWyBZF*yc+sBkX<}OgQxtW27iUOeWFX=L{U)@>LPNpf)BMF?vJSG7+mSJ(A^;@lc2vZOkokXRyIU2&nA$|TAtxu4urze^X1)aPaT>y9-d}c_g)5^!A=|C(<NX!Rfpsemct~2uizVaW}sUof@Rwj6AYM1?!?h?e67Nl?!OKOL$g|10wxHE)if^&BmbN9Dwl4;dB-UGaisYC@+dGu@*(?%em-j&YCycD$B$p@yPLaO(GZg~%woA<z#=L1Cts5-%}vdxe#FL@*O<ur4mv~G-bFw40-&%`)A#nLuum1|D`Gu>#B4JL3+;7~;|RDPC-gd%&om$z%xO`4`Ty05IL7U5ky!t272xGb2p_vlds`2x!&S6s*uaaAe0p@fAl|0gC-r}+<1CbO$lZf*)f9C(tZngJY3t!Jps(oT%?&}^8}rI*j$SMd<UBKb>*Dz?kr4uoh(*%sXnJjcC&?aWzHwly%vxI2$rUP|r;3{C=bO~-RyNgx)`SsTq|*pJJd1ft{vXs+daU~bL_*Nx_+eL;5D7R<@POd}7%J6@rXyD`mARAHq-C=ugqtgC3hs<(gEe%8%li85sI$bQ7~0E5&zQDJPH;5U?v>$ihgVp&voAx`^rMdMK^v#GPQgEIetNEIE))R0azbbAE|8lZ^P)>3!N;F40Wy65<S&skwIk0{SAj8$}#3-!yDak<?$E@!>AnYJ%-CEYTqKwGVSX?hLp2rJNVFN&nWLPy{V?WwZ;RVOE4T&l|}K~%%_IeBek9VC*aY>IVSvi{~K>wn!?NAqiO%_Qr{3+jcWm62w17xf*Lrkm_hN+)SrYIdDdXa~*;gqB|A{ho?NlD~Qy{p$i{vC}FNXDmOYkUBv~Bdo9O;Xp&^Y|vH$S$F(J)8ZATEttD&fB+#gC#A7&Cm{)k(W-o7NMzwT5nR<PSSt$(RSD~BqSI)sjQFfbdLku`Bs^zfXNXRjZUwG_s$5B5^LlxpD1s_fFIpbxMvoA1d98ser6uyqYYA1Eijsb>P%MWLC4Hf?Kl|l@>&u&%il|hUs>qs_kiNMI>0h~08N6ovs4B8FhKFE;m+B3XJ=2I#yTj>n0GL$U#aO_AgN`P~;Yi6v&^=X<1d{Ke>df^<v#;x!R%@j`MKGSgS-c%7@v6O~?g?bC0oAijN^=8KDIHOy$d{lI?4nvq%&;+jb`?SgT+{(BYHy?~I7PgHmKUBuqToY9x%JscyTz$Y?=%M%$JLn5!>V+HVQ<z;ej4yfs{=(*#9#1EY-akZ13hw<OffE)RakX7TCOls3SNwOnTm7+KNXv$8nYEfekDICv;w=l?w~PFv^C->8f$6#o13Qpb)zxP&WmvI%$bcF8tytGJ*tBLAJsv-tluL;ahKp)TPc8ma)6G~RNH>}3=?fm*O0QgKCBunyYKS}I#U9l#;A&-ta7+EF{lPhrX8}dN}Z*FA30tkN|my>yDBv*s}}BIL4B9*Ulk0nK^p^TQ4Bv%oNb5poV2q<tLdu@gcH<7no+SGnx5IIP(01PpkDraOcN{~Zn*A2+R-@xWc&uNRy&&9LV)MhjuQiEiNVPd`s1pT%%wyZ`V(q8jaLwp;^iP5FQ+z5Z)#Hx=|EVaQ5gq9ndAzK`O%&0o4}7)>1a~m*D?$+H^YD{cPu|MwOM0Ex0dJgC0NPkMxbW^v)%Cq_lb%#aF3Eaj7kJmX*cw;c`^Tr4)s`?Z=+}%r|+~&tEoP7Cy3R(11|34b3wn|Vczu%eC^9}1RZ>?-Gl*DYAEhRv*^nB-m1rQ!K%SZiT=Vy<lRRqVd(7oa%F-tdd!MWPHZ`lRtqMCIi`P6T4Vxan!a{OwJM`@%X<}_<vRP2=S@|rMS(>Ja(~S3Dx*|gS`<Q%9G-;CY3)T7eyz?4&JAL=+yWH#f^~)Ko7!DwAXwMZ;WsxO{_DnU%w9$6l%`(U8_E-us{Sz(Auf`*SN~2Sg6Vj{@^M#Pk+`LayaZ4Vvx2G?*GFh@-Feigh$M#GY3wYhu8dJu8%jP+cae=)a+h1Rt+a}UAo)KRtL`%A&oEvugAyfz(wneMfTkn@4R)Vr`ZZ%n=2JBGT+H?^UKIF()egfYl|&I9U4nU?V^4>QpF)vuKP#_LkPNx;E@x5bj8!WgOs?6_Y@?2|?A|Uq-P=3sI5oP%|MF79mQ`=g1X{{hsdO+WRXVtB70u;!CmaZ(ztX|9H2cj>v;WG&f%0`^Vb7>O>&@96F8CB(`ml!_gyihw)KNo6v#hpB<EA{0>c?g+%@caI(W39;o+3orcG=-|gWWdt7;lL^BGVvYq9PEZu$9nuIQd)UnPg!3K!x-%d(XwUaUWL|!s--wB#Fh)Gt{tbhu}vqfU2HaY2tRG13Bs8W2PTM;0~I|kP<ef6<MTDHI`LP|BiSLs+wyim-z=-$8)l1%89a<$k&DElr$1AFI7OtmErdCQUY|c5-Viq%5+q8Z1?iHdxr0d77Ju4U~B34o12dRbt~0caUyZA>IgJ0vv#6>EOMG2W$!sR$|vY{RHH|ZH`_6=N5@JoK7`oW8tj(4qlr)ut*G^LLEEk)6^bTUf(y^Gwo)CDYbaF6#$9ibYgh6J${QNLvyqY&46Q^tLRm0@TL(;YV<s=e{hTU|EBRb7edu*hnpOAPdHRh56rtKA2E=E`V$JFGs~saX98&kv0Nr6tE}y%^*j9wRc(QXlLKVej_5;(_k)pUX<?9#MLOF)$Rafgu`BuqzMIs)rXpD3NH8up)R)2PI+xGGnjFU7NhZ&4(84lQ+;lOpnH~}wVIB+@y(-_#uzEn;EG*8%@-3zLw!s*eO)1;vAxe$^&rx16oVM%BW<o3pj51sr?;JFoc7BW6?xIhM_5wyT{m2^eRnwGXF<YNGj$hBONn#d}niv%0)=)t~(QZYfA^{is%ezE--C>$wWo^3I;8&#+|6NlQC9(oq<q=fh|9y0f>)WA?Hjdp}p>>lMzy0Q+yGA;=QptOeofW^X<-P~&oO2=9)w^LN%U2cpZ@@iYj_v<an)wa9}?_^()&Y^CtET3Pi@^XBA*%tey>LV%kQ>O;$YJ|Q{>^JL}6O~XH%_rTBhXnhzd=c!;7vZ|GpJ%7OqAvoN6o++FO$2mob!A?-Ciw<-+d##H1|QV>QZU=9yY6}EuR|5UC5WQibhy(Th31L?ALlTN!AZiWiz<p9t)?XzC#>NCVQ=NRW0Q<YL-}%IAT{<R;apWZj)Yuzp?<ykFicmFh#dfbFjw<>6?kshX?oI2yvww!w71g&2k9lG=}pubTqPMcGK0IW5WpA14~P>>RiRzxi!kjNX|aag7r7IiHtWjv8HXYmpET0e0dS~_+*z(AE*G03p{@+=M7K>slTgR80_`v-{q3b=6|?&CqRy$*NKFz<%Ot_xOcJi#BmwEr?u_!<J!(lXx-1DZbfAkY1Sq<S3-G8NO(A229R+fDB*36MB{n*9fQNF}ivVythdmgSZKQxpg%!~>jGti@A%$nRb7S4M!4>NbbaSe~2rZc}iMhN~;P*t$HY2)dbBkD8RS%lXn>(n(R0r=ggALYZ7Yyqs5lwx!RpUIh{Ft6NM*jz_qPUg+1Lji2Dn)Uon16*%6qf=;0*XVB+ANA8wPfr{Q>5ts04ISsF``tQlL2?*a}qe%<Yh;xm=A!smivRfxj$Sth_mck+#fhS#5ZO|O;{yq+7VW!<l_ERXd^wlRuCpTaEU#4q$)^~yAjh;AD9snAqu>g9w^|aMNUk@{UPJz7;a%l${W-Kg4<|ppM@1-$kurA1{nM$Y&yxrS|O4TtD@cBW$el^Ep5r{^xSs{VzjD)0>0LC24kstUV@s-Hp^f~1YlQOl73d;9W^}>bAef$RqNt&xh;fc4XjmkiTAptU0z##SW8ZFYzy3~G2c?{Hh*yuY}s?b7T7Uch%96#PX$|o^@A<jvW2iWTZk*S+JY0o7NHchtwCW#7h`+8oNt$7q-Ix7K%pdnISU*uSv_?iMKnoe?jQAa2V7as*GJsXxvCUn($Z=jBCVX{??q!4rm?>nx|#@G7iT1bW^?_%2&4DxS4XmL6=h<YIz@)SumcrPOdpEDaLKw=iUsR2Hd%Z_#HaxEP(>DyDuFqT+G?K*MI@)I7iSNjmh_KtxafPcL<r;INLPt+Hn*kFIZ@80*if+!TMAvphPE#b$E&KuSat@pScZVu8*k$y-tulgQe4|9E#l<>_8_1q08cVWo=j?YoaK>N(uyerY<W@Gn-|5Em$aH!b(ZI&`&y9b*ecZ#YBk~hw8Wo$-ivJ%j@<;CffvNGdM3oqVrl#|I=Ox>7{-#ZJ}1!<Nd*cedfMWbq>kYh8NeI0N~Fwlx3j>g@__};3Dvgh+)O4Q?e6gf@Gjn<`UT{fhr{7Oioq_XS&Ejwea^&sz(%lRO%>C?oAnx+)^<Xw(7`**78;6c(1mH-YM~`EGk;NwcR4^{w31@}qO7@A@!C@7`k>Y{*QAmhG+IC=Q0U##PuFLAc@OMx#E5VwrT^QO1B1OeFkE@*CwpCvSYw?$!u`-fn!VEcomzzI>PbuUMGBM{QZx&ZKFQIYWeiz(nC2(?oN~~1vX7%OBi+S-(bRD`h!h@pA+B?_R~&_F-;8e(K$>mqU+jd#>X9JYhQAnrEtSNQQ3+e>)qJJs<^?9H>m=7Y>J;FGm9dI;_?z_-n)2agTI#4fOyBFJj!O0!i`uM;u|}oJ#8|PI-BWl{sUsVrQssYksZ=3J5&wuCwKCgZ>S$Ze1@`7#aNSr(o{Dt{Tq<g`=a^JR*D1Ye$VV1%mAsR~gcPL3MF*KaHpPrlyxf7v_z>CwH7q_0<_pl=0TIAsS;$g;p})Lf+QtVJ>HA7Nik@Z|!jhItVck(%9616E@RbT+bIff6XBkw@z^4^-Z-{CyxDsP4gNZG*@3!{BH3l-q6`4AYS-WNRRwf#k#B{7ZaBF=Py=CqI)25ILRmfeTii-6Vs|!`gJ|2Abw^q$4SJ#!$n-J%?h3<r^s_1P^GHau^&E+lhW_Z6>sBM`8*qb@Pb)z>lFDX>9FSA6Vgpb;1*7?Mzq{jwOUqO+bpuN!PtWZ6a(~Qg^r`BtEhWCLwK~9TsIM@RqKx4J39>;eSr~A9t)eDFr!6=upP_p%TwSq@RBTeDH;+qL=`Q(mZVwUae0!NWsiA!N@Bq?D%kC!R!PfKo!jZ$t>rl7T#$7^7tPTqQEPpN7|C6zi@3hWVZ6}`N5Y>IeQlpZj34b^Nnv{ksig^m=_NnNDqsHMbjZ%X{vjgFW+k+~kGj@Ay0Ym{OLFImxJ2!0A9hWCIOHRdj3Lx3X|nRja5la9bb^^mEAeKkR>A-yp*|6B7Tpe)2QXOnSdM?#`mnZW**OpBH%B42pkdi9tEy{UsinodT69u7y<>><pALeBa)$7yY$K$d7A1k@@BH&lgcp*%g9LP;CYjz|h&0T-B7^*yq=Vm_1gJfkT49`P5=Gb)`X8g*TEE0a_$k*aK&Q^k9W2u%}<@fsFmeiSdSxEH9(4bpegi~uAk=FUOSZhH^kkLc*%SIa=y{y)8U0PXR^KTS{d>C?OLM5lY{zw3dQhfuy)^wYb~UmoW{`T66&{9@|Q-FF{<{Ph0e%fm0;KYsY<yMKB7^2f&ycMI}!L&p6Y_w$b*-abCP{po{i!N>PMKYSlSpPN!2KK}gh+1=TnK74ud&3xxZi5nz8KRkW$*Ew+Q6UY9$-@SiugU45~3+wlf^({E`%YOXn{g=luMkjO`?&o~qxb!0Y>bKv$`|#o8m$zTs@137SXu=;J{`l_a$B&;w|NNwW`11MV(<e7*9)EtAXUEjC?;n0}_c-3q^s2ij2X%kp8{zKm2RBweKYaLd_x|yRhwuL6TK#l4J+z1K<K6!9FCXvRLwfq<oomwFySt|^@BZ-q;qK!H_edV@rgq(39^M6)dw}fLwP`>sYeoj!|JK9y8F)|f#j*K(l0^x49?T@LlH9)KD$fJB{J>wUgTi0L{%@zBy1mRVIev|puMWTA?I-sv{l~it?lrSYYXR1QNHhK7_4RL`9{+8+R4`B)Rs5enmNa|$50ze`mjsI~SK3y3X*Ru7(_*vfrO`XRwD-ulG)xKURTdhZl%9;~prb^q-8$$M8{3`yw)QA-TBAb4x$rXkrB32RwM{$81@clSrwd!1gvnyuxHg9;%Im#U_m*XUcY9fTlw#T{V#__hw%AMW^0MkBW5q`)_j>6t-}DSwe59>zI?ybY7tBXyxlX$|EyeX&2~++hwjTt$%u6FQFLx6rujj0vhEJU1O+Wc=M~&;JNaZkFGt-+UXt!-M!KL*63(bE1L%pBsGBX{Tul18FSoKqLTkI#Q{kaLKl>v}eaMqri+MR*C+JSLLUN>rGyPx0IpQoPY*u1JRg_R}99kSQc6PVD&rIt%Un4pmoZn#@#Ol#;mpzB7hM1fvIaj&cOM`|%yY?*=DGga1Xx+?v$Rd}e3@6XbtpUO(z>MG}MKhfxLoe)|YkFgfW@#WEBrGH9y)Y$#0_}O?Q@cy0Ofv4Sn>Xd)u`*)xG_Q$_kLltdSIK`i>{5KqIc(+{n<PgUXA3s05{roVY0w4VT>Wzm)^966;{qV&#?}x|F?(5~EX<R*h{4t=XsWBfOd^b|81jW@hnsYX~1A5yXzJ^^u>y9sG-tErxfqUI~{>SGzaQNLHKe`iKa;Uq73im>Vmv2qaJG5^qqn+C|@f+s$Otr>IJG^e@S8qZC0!hMu@?ZHcrcVqp=INu{$<!Zi-7)3U^g;jqSO4p4{~Lb)CNwsDuxrq7|K|VvpI^QG_OHMBt^eWN@a29im;LwO{r%tm`mf)9`&-|{{Fh`+beI0`U;XZH-QD}<cVGJ}=Vuc8|2Mz>`t7fO_w}!SvwUQBpXblNwC?M_a}Vr)OuuP)aPt@L$KU?un{WQ^um9%j#xHYM{f}S$?l)im?%TJ&`PJ|K*Vj|?W5btUxpX+~%JVX?vNOg{?yIM}@Dq1<aEsubzs<jJ>*mu>KYsF8-F<od?w@~o7fw6B`1JYX_dk92WxDF=E?o97oi?Ul^~*aq|J?j>zbjthjz)Kn?zew>a4#Rey#LcL@4kHemk;hJ^6(4)9(PQ6eE+Ap4R?=EcTW%QVB&ton>-q!Or`^_B$PEIJ=Z%6B3K71n9^=PP~2dR?xOrA;v>P*x`Ry0V9Am<k{8LxJ5DQF*qWB3Lbri9m}fx>*sU#RK5=Y3BM^k0($eofJpTCZ{WLG0-hZ6WZ`1KyhOIN?i2Tpo^ZxCxzWuwu|J~Oyp65lNe){yu?PpU&-2qOf9q0>~#%J2x>GLtn?q7fN4}SS~{rvW?zyA8Sp6)d*)^6qf;2zdnztcX<2kdm3^C<(gYLK8bXbJ~yTHqsRa|@u_g2HEV;!Q|(-W`H9rJKMnO<>iVFfVPON{u;i1JHEz8gb-<V(0okO1#=fiP!6uc;P1naBZ_RY0>LV)60jx`aGRs3nZ`wiVb_Uk?``9Hu)^^dY>g;v0tw@Z+-CtX~5#Tcxe5>`Z8W8pU3ie{q;BB{PwT@=QrPc`}IVxE3`;n?z6wR(j3TVP}ZFJ*9Tj_ax><>{?*)IH{IiR!c9~caKFO+#U@Kile1H~PbHO_40|&jzgjmQaNYW(kyB+^*9vX2K#8)2A?8zU@x#UL(!`Pz)#X6Ni)|FdT_i8_FD{?<(#GAJT3$Ub?IJJh*{ZH(``+2zTW2r#%MG@#fAibF``^=7?Z&?F;&J(;mtX3W&!P^Ejg3+1qxJ5sFSSA76|~{io-TQ7;JJ!MVQYZ?t>LTYUAUG_B1Vm>n?%y&*VrW1TZ7ze4aNH^dKcjRXKr=hIv1BTS!x!iPJWdpG)!sl!o~o+>{9W$mKuZ9Rp7D@__cr+R{_TNZjLCnL7Z^hTDHgC2UNTd;>`OnNk#VGhZkQBMfYmhT6Dr{$PTQA#V2v%YRIWei>$APSYHjr6|aW>_|=;~e*FCSZyzUu(9_h9A0Pkq?Z?mGKYaGF>hOtQO;0gCLeDw=`29l&VgBvcH}dxR<ZalLwy{6spINK2twEI?mxAmyY@<8O1}^wktTOAg`ZJq4-Ii{_Kl6AMilqLlmsRW4f23FF-qGjwk3zoLb3Ab^|Fg~&7ey@fhGs2LnU318N8p|eQ1r&xpGCZXb?!3E<L^Vr`EJ;*Jw=IuCMl4kk^*W<Km5-!{lr?cmW$+bMrK}AE%ne)s1DHnlG3cf;xeRlV??vn%{G12V{FLwnQH^I;lDdvl8f|np)Qdug9f4GgITU5U~R0xpCNvnXpEK1I*~coM0do+rZAMleftl$t?f0oHaU;>!q&E~@HAs~=KFJbzZ|=-2)MKwgPiIklx0jxBlP|X0fw^h@k3se^`**BD%h*Iz<lN<=16v^oXVQ8WhvwEuQo6wB}a3=ke3@Rfr2h#fsAGYUGqbTRA1$nPT1S`l8ffYkBNjLQO&v7NIlh63CXRMI9BRTC>C6;nWXWU?24SSb?WC`OarSq1Z`xt*IW{mW7Q6N$cS(De8>{GCfZvo2_3BNh}gfyvUrOV?~6rIeBMWIN5ogzN3pt((ySEORPZ*7;Db8(6j=XY)FYcZTIJ>1_Pm{ebcE!WtKys*J3+$Ks67asd>ly1Qnnz}S++xt)hfGYO&gG8h*q*OO_{oj+2+RM9(qVtJpQ~r6rBKKlADP2@=UQBC4L;t|Cc~NNLHXDry6sN%&XF&$p$H1L~Rs<efVP=W3YYf-#kr`Uks!7%ywC_HdeJD0n0!N2f8d_n2;tUHjm}!wv2bROh0Ear=`j`J=^+1$%iklk%4@=u1d=Hn3PQmIa4>O|MC@mHJ7NY=Fj+5aSAJkD$KV(zI&J;$?BI)G3UKYrhs&Q5zCA382U*3x_E`$!@T%QLQP+0>D*Ecx9OtSEJ&Kgd8vzLQy^LB;`+9)d)W01S9go^@gDl@Mb<%6=;3xSP<j}&W`2J7{Nx7w+fN_gKl)a!>Te(3eSZJ=@bqOVXTE#*@cl0wxSVQi@1|PZk00*deYt!8@XlRk*nheE_`_YSlfIiun(n^*(OuwgnEUGS=`PT<|Eo{o+=a3hU#1KEmv=w9cm4R&k9VQI2ui=~%~WCY;1`1Le){t9hadce%lq>5(~m#C`~0VAB8JbJ@<Y)ic1pBgE`ORp;9Ps<PgWnFzJ%KDf1frjpT3#Ui=W}&KTeh46Wn(wa+cGbs%=W|vB`V*<vsE_e*f)1z5Dd`>C1yJ>fqDP<Zo$~G`%FXL)Na?BV6^!)3layvQ3`=V*_Q{sn|R$bm{UImAnPgyRhw%zh~?Icp_J1BVoNmV$~tvy17IC%T<S_wr^U;?pb=r*Il~2NoS8~d6O=8N|hdy{~ZgTYRyk8_7Gs*#Y+#j9o*?(X%zC($W6MZiro{Fe9qFnggBNlKFVEMPb{@`No~5MO3lN(dFw94_e_s2zDHc%W6BfDW>0KO&}fW9SkElavW}0*Y@d^fy~1>ww0m`Vljs_VytrN@L`j_x{~BFf&o#WvHQdfMEY3CF?jjcF8eW#fN*7tNi^-a38vT;1e(9xKdebXiTC$<FeCX0x#P;L@Sr~_W8Hcjb8MR*FFAMy3eJ|YX>1*G#Ni%A*ycZ@TnD~zJw3?>Ix-*S&#y6Xky!1hCJ0VM(RP&Ks-jc28JI@3Qt2vT(UA~?<m$hNLG{i|hb)m4{l{&P%hnLs8a*xz~X_$$xat>6vM{=M?`J5s4i1lnrz_KoF`PPjUoU4(2Hk&!iGBwQv%03JB(j`{jlys>}Er>VtXk`DRsjcgkB^pZo&|gtj1RQ!a`E6cy5NJG_Y_uh}ftMeRDegLre&~_Kxw_QW7Uyi`fVAI*HK2r18*rPCJc-J@N9vQ{Ie?|EWF#yq<k21_hdfRnTQa>1rQN1;Y>D+8xt#2_2RrOWF<5*q?bW#bOj>=>BYnx{d+Ui5d(U>BhiM+UTLa7t46u9(69*VCM-i}gD(Kr+<a+8~P}vrg$<m=sw2;3nJ(L~TubU{jvDZr+ScrML->Ft#mUpD^Qn&je`#`cB*-E%9-CNn}LAB4@9+<A3M8QZ0SZT(xllH>tfZOp56d&nAwL#S`@Y0f7fh2v~xx#@6XVxBU$Cj4&VEJHDj&K%n6_Qq4B?h(*E=sGEXl;YVnN&GuHCL%tU*y%zaoIP#MuHL9P{C%bdH3;cJ7Bvyp!varM+$eFu~%D$yOI)GCPX0g(1u5z7W;#b7*A>RKn%c-JpN08AKCKU0YA2oumL}`dYz4<I+M12L9@U2#fqd#yyS(3RLAOsvbPgsC-N5!mvZdxgt@-Sy^llkK8V9B?M`N)xYFWY)T*4r`-=8l<Vc@ZNJ&!qls!win=Ijk(88)Gcy)7KVCM+iU|rJFVD-#=^=UvkbwvrncaE?PLhKIuG|#ccpijp+cH5igC{ya{)-iw9=^AC4ze<QVeTGZ0Ybuf$0$O<=EME7ywlXzBiFA$WLgMbo^f@ehL-9$7LKY;+=G2}=F`FY=9T6khX;~Oh#W;yBc4H?_qMA82-s%lp-~7k`SA_?$>co0**`*V9(+OKbjkdLs*dmo|C-bSA$+h+~5l43sPKucn2@oClk=mV2*yO@ffh|u3Sb6rhV<$y&3+&~mx!z$I>1M}<QaqA6cd)e-)aDM9IbgdfxV&c@%11W^ho4TtVdIP3h8+PHf*WiZZlFp%674Mf@}@juv3H=c#RH9?c5H*tlI6RwenW{~&|EAoZ&4kqMPc!?)GnD<i2&3y7lk9iekNswb@<f<igj-n)+>O#^g(VrA&aoH9pNkD&YiPzDeG&Jk%i4ZZT8g*PQWctKwBF6%>V$Fz{Ta!=-qro!G{2vXcPxG*ZiipLp7H-rLhpTx3q~O352+}ZYV~i^FoE#0<BCKlp_k|bOjb^Anhll4;~nDwm#*+kng@bbXL;SFxPjAW}PeAl~Sc7f%dWL$R==hS;qKw8RNFe<S525ZK*5$%UFtIKsNiNMk)|2J@LI)fl!_(x-{EWvm<&Ws>#bErpYeCa_6ze_GG=o%pBwwwGY*@N&2ds0SeK-_OP-e!%CGo#I`Z4G5~7!xL%x>^Tl70HWYcdT4!g7?aeQ&oMdF@Tp7z^RHKw<q+OvGC(Dr-03GV%0MyTB$u7@x)g3)TKoVsvDO<2hmZ4-vQl>dc6hF%H<n3BfUS?nI<zYqlIy{soYw=e|xCM7hJ49b9cGW2{@^~bDoblqs*-OQ8){Vx-NMSFUoROVtm>MbP$n$)}Osp*D#Z^baZu?>A>)TOO=hM)596?IbIR(orm!Q-Okz#opj@S#u!8&N&$a^1$y1G~%RFbd%_|==oN&fon<A)y}K2NTsKfHVY^x#!a9zJ{@EMmPF_v8CNz5Vg=UrX+;L8%+ouC_r%VwT39z8B}CzR%5p63U&u&-D0>O6r>3AWgkee3T?J^>RPYE)a_+54&dtQ{K>SPHs1f`^@DzJ*u*MmHjMn0(H{>(k^+WmrU*)a~lFAH5=*8*7uNkFXZh8mHkQD&F&M+9IvXLx7*&Uv{POXi_mUCZ@0O}l>q(HY_F4;e6*)*#Ae(3+`?dWx6Qp?S*;KnE$NL`_bN3T%A&IOxjKE;Xv_>UOx|dBq+ELH`=v>(R`gc8A(%ESEsHYuw$^HWZ}QnH@@A`hT;B{rvvtoxk{c+gq}}RXth%&V^WL+|0Pt_lTP^RC!DD?4kkDvDZnTdNte2@p;^1DaR)W}Oai34cO`Cb{nn7x`Z8n-MO=fQ0OXiwTNt4|IBJ*V;k)q)1)nzpq@jmlC(pFX4eevF2Z#D><hGTMaRVxuHk#02`b*f~^PGy#uT`hg#_(^IhC$`j0!R!-twn*oSP9j^R^M<Zg4v;I&C_`*FQrj)>H_~I5ReJN;mjy4Ax?-yv3~LoD>c9{uG+WdMhFOVpZMMX*R!jOI$u+`MwotFc$kJx#<HxM`#LbUM%~sS|Xty7*oCe&kn5m<wbbrBIwQjw=Y}C+5&DPXr<NZdEEw-B7+gvN}(rUT-5pFicb*D(JHpEuD;hW3gnQTVpighC0VVYw^-RE<Hdb4e-+36O;H+Su_#qh28-(`!**FU}5V#I1C&!Lk$|Ga<a&STRV>+!=sm5w+5+~oclrH!L1;Pwor6Ll)z)t_cpA+Dw%CfEK9<L(DHF$Yopq(wP)`lw?4W%Z+Qisf)I#eun;NHqTQ`P=~SyyicjH$Hz670tSu<v2{Dd6IrUsKEaL9p)LB5Gw*3grPW#LD=#~XM&&E$ER7MOA;>d>EfrGDN+G!y4?WNJpex45x{^NKm^JK$WXuR8;p$xMfK_YsbAW1i9_4$IZPMfbXZq`j_n#J+`nuL9&F~zcAR1HsIRMo48t?_SNLb#{+x7_VUdbo`5-a%%8xAwV@u5+%PAk54lab^*jge{>yd?FU||?n{$%IJl^@}__p$4NwS06su4HXgK^Rp$3?~S~3BzcTVKDh-PouxtjAS@1ElBzvqd3_OS0OfUCRtj)VtxF>)5GVVAHIM4^v8#XPjBCUe0qBOhd;gj`SI!T5APphq-bgk%kJ1}BKph~hw%J(=z+hH(~rf}h-m@Q;VIkrm{oYp#y@WBlMOyd_2uES>&(0NZ$Cf$;AMK>e)sU<>Ejen`ttdw2Y1DHfBfimeZRbOZJhe`hxZ@9`{zl)K74im-P6xrvVHp3+fVNvKVN<r{u!_EH}mb6pFV&1=wodDqWn8=8H4HCueLwnwI5*Z2cq@^S^I&i{Xo}#U}`_Gl^-~OT=@ZHcj+QR`}_PG@v0EReCw_CraPJbdv(owud*E;V|r=&?bSQdPhWj&b>-By&kt@N{_f$&V8{3S>d%%QPTH|=pC11$G${S|>Y9ACtiHFpHmU)q*Dl{%x4Wc8TmRwe-9>rZIqW(|Tho8WcdsE!{*C3T$N&4&<M;1^yzlSRf5t1q`muz0f1iINUbRf^r!Q_M`pfd~gzGLd{OQyC$4O*6s`<W6gA7qjIRS<7Tc3Y=@AbbQK0Q8t{QlwX<M(&}<xbxHxBqs>-aJ45KSv`r#{')))

COMPONENT = 7

_STATES = {}

_CROPS = ('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON')

_FIRST = {'WHEAT':2,'CARROT':2,'TOMATO':8,'STRAWBERRY':10,'MELON':10}

_DEFAULT_LAST = {'WHEAT':27,'CARROT':27,'TOMATO':20,'STRAWBERRY':18,'MELON':18}

def _quadrant(cell):
    return ('N' if cell//10 < 5 else 'S')+('W' if cell%10 < 5 else 'E')

def _features(observation, quote=None):
    quote = quote or observation
    day = quote.get('day',observation['day'])
    shops = quote.get('shops',quote.get('town',{}).get('unlocked_shops',[]))
    prices = quote.get('prices',quote.get('market',{}).get('prices',{}))
    choice = TEMPLATE['crop_choice']
    demands = {}
    for shop in shops:
        for product in choice['shops'].get(shop,[]):
            demands[product] = demands.get(product,0)+1
    values = {'day':day}
    for product,base in choice['price_bases'].items():
        values['demand_'+product] = demands.get(product,0)
        values['price_base_'+product] = prices.get(product,base)/base
    return values

def _predict(rule, values):
    if rule['method'] == 'constant':
        return rule['prediction']
    if rule['method'] == 'lookup':
        key = json.dumps([round(values[name],2) for name in rule['features']],separators=(',',':'))
        return rule['table'].get(key,rule['prediction'])
    node = rule['tree']
    while 'feature' in node:
        node = node['left' if values[node['feature']] <= node['threshold'] else 'right']
    return node['prediction']

def _cutoffs():
    cutoffs = dict(_DEFAULT_LAST)
    for row in TEMPLATE['endgame']['last_planting']:
        if row['fold']=='train' and row['counts']:
            mode = min(row['counts'],key=lambda day:(-row['counts'][day],int(day)))
            cutoffs[row['crop']] = min(int(mode),_DEFAULT_LAST[row['crop']])
    return cutoffs

def _animal_slots(quadrant, mix, day):
    cells = [c for c in range(100) if _quadrant(c)==quadrant]
    candidates = [slot for slot in TEMPLATE['animals']['slots'] if slot['cell'] in cells]
    desired = {}
    for animal,count in zip(TEMPLATE['animals']['mix_order'],mix):
        structure = 'COOP' if animal=='GOOSE' else 'PASTURE'
        def score(cell):
            matches = [s for s in candidates if s['cell']==cell and s['slot']==structure]
            support = max((s['support'] for s in matches),default=0)
            species = max((s['species'].get(animal,0)/s['n'] for s in matches),default=0)
            timing = min((abs(s['day']-min(28,day+2)) for s in matches),default=30)
            distance = abs(cell%10-4.5)+abs(cell//10-4.5)
            return (-support,-species,timing,distance,cell)
        available = sorted((cell for cell in cells if cell not in desired),key=score)
        for cell in available[:max(0,int(count))]:
            desired[cell] = structure+':'+animal
    return desired

_MILK_SHOPS = ("ICE_CREAM_SHOP", "PIZZA_SHOP", "SMOOTHIE_SHOP")

# Animals the reference team keeps by day 12, by yarn stores (sheep) and milk shops (cows) open early: 0, 1, 2, 3+.
_HERD = {'SHEEP': (3, 9, 15, 20), 'COW': (5, 7, 10, 14)}

def _opener_cells(day, observation):
    cells = list(TEMPLATE['opener'][min(day,5)]['cells'])
    shops = observation.get('town',{}).get('unlocked_shops',[])
    if day < 3 or not shops:
        return cells
    first, final, early = shops[0], TEMPLATE['opener'][5]['cells'], TEMPLATE['opener'][2]['cells']
    near = lambda cell: (abs(cell%10-4.5)+abs(cell//10-4.5), cell)
    if first in _MILK_SHOPS:
        # two more cows, on the strawberry cells nearest the shed (from day 4, when the reference adds them)
        extra = sorted((c for c,label in enumerate(final) if label=='STRAWBERRY'), key=near)[:2 if day>=5 else 1 if day==4 else 0]
        for cell in extra:
            cells[cell] = 'PASTURE:COW'
        if day == 4:
            # the cell of tomorrow's cow keeps its wheat today instead of taking a strawberry
            for cell in sorted((c for c,label in enumerate(final) if label=='STRAWBERRY'), key=near)[1:2]:
                if early[cell] == 'WHEAT':
                    cells[cell] = 'WHEAT'
    elif first == "YARN_STORE":
        # sheep instead of the two later cows, and one more sheep on a strawberry cell
        later = [c for c,label in enumerate(final) if label=='PASTURE:COW' and early[c]!='PASTURE:COW']
        for cell in later:
            if cells[cell] == 'PASTURE:COW':
                cells[cell] = 'PASTURE:SHEEP'
        if day >= 5:
            taken = sorted((c for c,label in enumerate(final) if label=='STRAWBERRY'), key=near)[:1]
            for cell in taken:
                cells[cell] = 'PASTURE:SHEEP'
    return cells

def _desired(observation,state):
    day,step = observation['day'],observation.get('step',observation['day']*24+observation['hour'])
    farm = observation['farms'][observation['player']]
    opener = _opener_cells(day, observation)
    owned = [c for c in range(100) if farm['tiles'][c//10][c%10]!='LOCKED']
    if day<=5 or COMPONENT<3:
        early = {cell:opener[cell] if opener[cell] not in ('WEED','LOCKED') else 'EMPTY' for cell in owned}
        if day == 3 and '_feed_cell' not in state:
            # One more strawberry on day 3, on the wheat nearest the animals: its wheat is the morning feed.
            tomorrow, later = _opener_cells(4, observation), _opener_cells(5, observation)
            near = [cell for cell in sorted(owned, key=lambda c:(abs(c%10-4.5)+abs(c//10-4.5), c))
                    if early[cell]=='WHEAT' and tomorrow[cell] in _CROPS and tomorrow[cell]!='WHEAT' and ':' not in later[cell]
                    and isinstance(farm['tiles'][cell//10][cell%10],dict) and farm['tiles'][cell//10][cell%10].get('crop')=='WHEAT']
            state['_feed_cell'] = near[0] if near else None
            if near:
                state.setdefault('_advance',{})[near[0]] = 'STRAWBERRY'
        early.update({cell:label for cell,label in state.get('_advance',{}).items() if early.get(cell)=='WHEAT'})
        if 3 <= day <= 4:
            # no wheat is replanted where tomorrow's animal goes
            ahead = _opener_cells(day+1, observation)
            for cell in owned:
                if early[cell]=='WHEAT' and farm['tiles'][cell//10][cell%10] is None and ':' in ahead[cell]:
                    early[cell] = 'EMPTY'
        return early
    phase = next(key for key in TEMPLATE['phase_cells'] if int(key.split('-')[0])<=day<=int(key.split('-')[1]))
    desired = {}
    fixed = {row['y']*10+row['x']:row for row in TEMPLATE['phase_cells'][phase]}
    for cell in owned:
        record = fixed[cell]
        label = record['cell']
        desired[cell] = label if record['class']=='FIXED_CROP' and label in _CROPS else 'WHEAT'
    expansion = state.setdefault('_expansion_animals',{})
    for quadrant in farm['unlocked_quadrants']:
        if quadrant=='NW' or quadrant in expansion:
            continue
        rule = TEMPLATE['animals']['models'][quadrant]
        quote = state.get('_land_offer',{}).get(quadrant)
        predicted = _predict(rule,_features(observation,quote))
        mix = [int(n) for n in predicted.split('|')] if predicted else [0,0,0]
        expansion[quadrant] = _animal_slots(quadrant,mix,day)
    for cell,label in enumerate(_opener_cells(5, observation)):
        if cell in desired and ':' in label:
            desired[cell] = label
    for slots in expansion.values():
        desired.update({cell:label for cell,label in slots.items() if cell in desired})
    # The herd follows the shops, as the reference team's does (169 games): about six more sheep for every
    # yarn store open by day 12 and three more cows for every milk shop open by day 9; shops that open
    # later add nothing. Extra animals go on free crop cells nearest the shed; slots beyond the target that
    # hold no animal yet go back to crops.
    shops = observation.get('town',{}).get('unlocked_shops',[])
    herd = {'SHEEP': _HERD['SHEEP'][min(3,sum(s=='YARN_STORE' for s in shops[:4]))],
            'COW': _HERD['COW'][min(3,sum(s in _MILK_SHOPS for s in shops[:3]))]}
    extra, dropped = state.setdefault('_herd_extra',{}), state.setdefault('_herd_dropped',set())
    def animal_on(cell):
        tile = farm['tiles'][cell//10][cell%10]
        return tile.get('animal') if isinstance(tile,dict) else None
    for cell,label in extra.items():
        if cell in desired:
            desired[cell] = label
    for cell in dropped:
        if cell in desired and not animal_on(cell) and ':' in desired[cell]:
            desired[cell] = 'WHEAT'
    for animal,target in herd.items():
        live = sum(animal_on(cell)==animal for cell in owned)
        waiting = sorted((cell for cell,label in desired.items() if label.endswith(':'+animal) and not animal_on(cell)),
                         key=lambda c:(abs(c%10-4.5)+abs(c//10-4.5),c))
        if day > 13:
            # no animal is bought this late (its product would arrive into low prices), but one already bought keeps its place
            private = observation.get('private') or {}
            target = live+private.get('shed',{}).get(animal,0)+sum(inv.get(animal,0) for inv in private.get('inventories',[]))
        for cell in waiting[max(0,target-live):]:
            desired[cell] = 'WHEAT'
            extra.pop(cell,None)
            dropped.add(cell)
        short = target-live-len(waiting)
        if short > 0:
            free = sorted((cell for cell,label in desired.items() if ':' not in label and cell not in dropped
                           and fixed[cell]['class']!='FIXED_CROP' and not animal_on(cell)
                           and (farm['tiles'][cell//10][cell%10] is None
                                or isinstance(farm['tiles'][cell//10][cell%10],dict) and farm['tiles'][cell//10][cell%10].get('crop')=='WHEAT')),
                          key=lambda c:(abs(c%10-4.5)+abs(c//10-4.5),c))
            for cell in free[:short]:
                extra[cell] = desired[cell] = 'PASTURE:'+animal
    seen = state.setdefault('_animal_seen',set())
    retired = state.setdefault('_retired_animals',set())
    for cell,label in list(desired.items()):
        tile = farm['tiles'][cell//10][cell%10]
        actual = tile.get('animal') if isinstance(tile,dict) else None
        if actual:
            seen.add(cell)
            if ':' in label:
                desired[cell] = tile['kind']+':'+actual
        elif cell in seen and day>=12 and fixed[cell]['class']=='ROTATING_CROP':
            retired.add(cell)
        if cell in retired:
            desired[cell] = 'WHEAT'
    cutoffs = _cutoffs()
    if COMPONENT>=4:
        # A rotating cell keeps the crop growing on it; a free one takes the crop furthest below its
        # shop-weighted target share. The choice is held until that crop is planted there.
        choices = state.setdefault('_cell_choice',{})
        weights = _crop_weights(observation,day,cutoffs)
        rotating = [cell for cell in sorted(desired) if ':' not in desired[cell]]
        counts, free = {}, []
        for cell in sorted(desired):
            tile = farm['tiles'][cell//10][cell%10]
            if isinstance(tile,dict) and tile.get('kind')=='PLANT':
                counts[tile['crop']] = counts.get(tile['crop'],0)+1
                if cell in rotating:
                    desired[cell] = tile['crop']
                    choices.pop(cell,None)
            elif cell in rotating:
                free.append(cell)
        def neighbours(cell):
            x,y = cell%10,cell//10
            return [nx+ny*10 for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)) if 0<=nx<10 and 0<=ny<10]
        for cell in free:
            crop = choices.get(cell)
            if crop is None or crop not in weights:
                crop = 'EMPTY'
                if weights:
                    total = sum(counts.get(c,0) for c in weights)+1
                    around = Counter(desired.get(n) for n in neighbours(cell) if desired.get(n) in weights)
                    allowed = [c for c in weights if counts.get(c,0) < weights[c]*total+2]
                    crop = (max(allowed,key=lambda c:(around.get(c,0),weights[c]*total-counts.get(c,0),-_CROPS.index(c)))
                            if allowed and around else _quota_crop(weights,counts))
                choices[cell] = crop
            counts[crop] = counts.get(crop,0)+1
            desired[cell] = crop
    for cell,label in list(desired.items()):
        if label in _CROPS and day>cutoffs[label]:
            desired[cell] = 'WHEAT' if day<=cutoffs['WHEAT'] else 'CARROT' if day<=cutoffs['CARROT'] else 'EMPTY'
        if day>=28 and label.endswith(':SHEEP'):
            desired[cell] = 'EMPTY'
    return desired

# Cells the reference team holds with all land open, by how many open shops take the crop (0, 1, 2, 3+).
# Wheat stays at about 26 whatever the shops are.
_SHOP_TAKES = {"STRAWBERRY": ("ICE_CREAM_SHOP", "BRUNCH_SPOT", "SMOOTHIE_SHOP", "FARMERS_MARKET"),
               "TOMATO": ("PIZZA_SHOP", "FARMERS_MARKET"), "CARROT": ("PET_CAFE", "FARMERS_MARKET")}
_MIX_TABLE = {"STRAWBERRY": (11, 19, 28, 35), "TOMATO": (5, 12, 17, 25), "CARROT": (0, 4, 7, 7)}

def _crop_weights(observation, day, cutoffs):
    """Target shares for crop cells: a fixed base of wheat plus what the open shops take."""
    shops = observation.get("town", {}).get("unlocked_shops", [])
    weights = {"WHEAT": 26.0}
    for crop, takers in _SHOP_TAKES.items():
        weights[crop] = float(_MIX_TABLE[crop][min(3, sum(shop in takers for shop in shops))])
    if day <= 7:
        weights["STRAWBERRY"] = max(weights["STRAWBERRY"], 30.0)
    weights = {crop: w for crop, w in weights.items() if w > 0 and day <= cutoffs[crop]}
    if not weights:
        return {}
    total = sum(weights.values())
    return {crop: w / total for crop, w in weights.items()}

def _quota_crop(weights, counts):
    """The crop furthest below its target share (deterministic)."""
    total = sum(counts.get(crop, 0) for crop in weights) + 1
    return min(weights, key=lambda crop: (counts.get(crop, 0) - weights[crop] * total, _CROPS.index(crop)))

_WORKER_CROPS = {
    "WHEAT": (2, 4, 6, 0), "CARROT": (2, 3, 4, 0),
    "TOMATO": (8, 11, 4, 1), "STRAWBERRY": (10, 16, 4, 2),
    "MELON": (10, 12, 6, 0),
}

_ITEM_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80, "GOOSE": 300, "COW": 400, "SHEEP": 500}

_WORKER_FERT_AGES = {"WHEAT": (2, 3), "CARROT": (2,), "TOMATO": (7, 8, 9, 10), "STRAWBERRY": (9, 10, 13, 14)}

_WORKER_PRODUCTS = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}

def _worker_distance(a, b, size):
    return abs(a % size - b % size) + abs(a // size - b // size)

def _worker_move(cell, target, size):
    if cell // size != target // size:
        return ["SOUTH" if cell // size < target // size else "NORTH"]
    return ["EAST" if cell % size < target % size else "WEST"]

def _worker_water_due(tile, day, basic=False, fertilizing=False):
    if tile.get("watered_today"):
        return False
    crop = tile["crop"]
    first, last, cap, interval = _WORKER_CROPS[crop]
    age = day - tile["planted_day"]
    if interval and age >= last:
        return False
    if basic or tile.get("consecutive_unwatered", 0) >= 1:
        return True
    if not interval:
        return (last + 1) // 2 <= age <= last
    active = fertilizing or tile.get("fertilized_until_day", -1) >= day
    return active and first <= age + 1 <= last and (age + 1 - first) % interval == 0

def _expiring(tile, step):
    """Holds product and starts to rot within the next day (or already has)."""
    limit = tile.get("max_lifespan_step", -1) if isinstance(tile, dict) and tile.get("kind") == "PLANT" else -1
    return limit >= 0 and tile.get("yield_units", 0) > 0 and step + 24 >= limit

def _worker_fert_eligible(tile, day):
    return (day >= 6 and isinstance(tile, dict) and tile.get("kind") == "PLANT"
            and day - tile["planted_day"] in _WORKER_FERT_AGES.get(tile["crop"], ())
            and tile.get("fertilized_until_day", -1) < day)

_ANIMAL_RULES = {"GOOSE": (4, 1, 4), "COW": (8, 2, 6), "SHEEP": (6, 3, 6)}

def _harvest_feed_keep(tiles, desired, day, hour, carried):
    """Days 3-5 before noon the animals are fed with wheat harvested that morning from cells being
    replaced, and the shed wheat is sold. Returns the shed wheat still to keep for feed, or None."""
    if not (3 <= day <= 5 and hour < 12):
        return None
    units = sum(t.get("yield_units", 0) for cell, t in enumerate(tiles) if isinstance(t, dict)
                and t.get("crop") == "WHEAT" and desired.get(cell) != "WHEAT")
    need = sum(isinstance(t, dict) and bool(t.get("animal")) and not t.get("fed_today") for t in tiles)
    return max(0, need - units - carried)

_CARE_PRICE = 100   # product price below which an animal gets no feed or care between productions
_NOW = {}           # this turn's market prices

def _animal_service(tile, day, tight=False):
    """(feed, care) worth doing today for this animal."""
    animal = tile["animal"]
    if animal == "SHEEP" and day >= 28:
        return False, False
    first, interval, cap = _ANIMAL_RULES[animal]
    held, bonus = tile.get("yield_units", 0), tile.get("pending_care_bonus", 0)
    since = day + 1 - tile.get("placed_day", day) - first        # >= 0 and a multiple of interval: produces tonight
    tonight = since >= 0 and since % interval == 0
    remaining = 1 if tonight else (-since + 1 if since < 0 else interval - since % interval + 1)
    urgent = tile.get("consecutive_unfed", 0) >= 1
    if day + remaining - 1 > 28:                                  # no production left before the season ends
        return False, False
    needed = cap - 1 - held - bonus                               # bonus days still useful before the cap
    # Between productions an animal is fed and cared for only while its product sells for more than the
    # feed and the two turns cost. With the price down, the turns go to the crops and it is fed when hungry.
    if (animal != "GOOSE" and day >= 6 and since >= 0 and not tonight and not urgent
            and _NOW.get(_WORKER_PRODUCTS[animal], 999) < _CARE_PRICE):
        return False, False
    if tonight:
        return (bonus > 0 and held < cap) or urgent or not tight, not tight
    want = needed > 0 and (not tight or remaining - needed < 2)
    return want or urgent, (want or urgent) and needed > 0

def _worker_plan(tile, label, day, hour, inventory, stock, seeds, basic=False):
    remaining = (23 if day == 29 else 24) - hour
    if tile == "LOCKED" or remaining <= 0:
        return []
    if tile is None:
        cash = seeds.get("_CASH", 10 ** 9)
        filler = ([["PLANT", "WHEAT"], ["WATER"]] if seeds.get("WHEAT", 0) > 0 and remaining >= 2
                  and 6 <= day <= 24 else [])
        if label in _WORKER_CROPS:
            if seeds.get(label, 0) > 0 and remaining >= 2:
                return [["PLANT", label], ["WATER"]]
            return filler if cash < _ITEM_COST[label] else []
        if ":" in label:
            animal = label.split(":")[1]
            if inventory.get(animal, 0) > 0:
                return [["BUILD_" + label.split(":")[0]]]
            if stock.get(animal, 0) > 0:
                return [["NEED", animal]]
            return filler if cash < _ITEM_COST[animal] else []
        return []
    kind = tile.get("kind")
    if kind == "WEED":
        return [["DIG"]]
    if kind == "PLANT":
        crop = tile["crop"]
        first, last, cap, interval = _WORKER_CROPS[crop]
        age, units = day - tile["planted_day"], tile.get("yield_units", 0)
        if interval and age >= last:
            return [["HARVEST"]] if units > 0 else [["DIG"]]
        jobs = [["HARVEST"]] if interval and units > 0 else []
        fertilize = (not basic and inventory.get("FERTILIZER", 0) > 0
                     and _worker_fert_eligible(tile, day)
                     and remaining >= len(jobs) + 1 + (not tile.get("watered_today")))
        if fertilize:
            jobs.append(["FERTILIZE"])
        if _worker_water_due(tile, day, basic, fertilize):
            jobs.append(["WATER"])
        if not interval and age >= first:
            threshold = 5 if tile.get("fertilized_until_day", -1) >= day or fertilize else 3
            gain = (2 if tile.get("fertilized_until_day", -1) >= day or fertilize else 1) if ["WATER"] in jobs and (last + 1) // 2 <= age <= last else 0
            ready = age >= last if basic else (age >= last if crop == "CARROT" else
                    min(cap, units + gain) >= (threshold if crop == "WHEAT" else cap) or age >= last)
            ready = ready or day == 29 or _expiring(tile, day * 24 + hour)
            if day <= 5 and crop == "WHEAT":
                # replaced only once its seed is held, or when its wheat is this morning's feed
                ready = (label != "WHEAT" and (label not in _WORKER_CROPS or seeds.get(label, 0) > 0
                                               or seeds.get("_FEED", 0) > 0)) or day == 5 or _expiring(tile, day * 24 + hour)
            if crop in ("WHEAT", "CARROT") and label != crop:
                cash = seeds.get("_CASH", 10 ** 9)
                if label in _WORKER_CROPS:
                    ready = ready or seeds.get(label, 0) > 0
                elif ":" in label:
                    animal = label.split(":")[1]
                    ready = ready or inventory.get(animal, 0) > 0 or stock.get(animal, 0) > 0
            if ready and units > 0:
                jobs.append(["HARVEST"])
        return jobs
    animal = tile.get("animal")
    if animal:
        release = (animal == "SHEEP" and day >= 28) or label == "EMPTY" or label in _WORKER_CROPS
        if day == 6 and (tile.get("yield_units", 0) > 0 or tile.get("fertilizer_available")):
            return ([["HARVEST"]] if tile.get("yield_units", 0) > 0 else []) + (
                [["COLLECT_FERTILIZER"]] if tile.get("fertilizer_available") else [])
        jobs = []
        feed, care = (False, False) if release else _animal_service(tile, day, day <= 5)
        if feed and not tile.get("fed_today"):
            if inventory.get("WHEAT", 0) > 0:
                jobs.append(["FEED"])
            elif stock.get("WHEAT", 0) > 0:
                return [["NEED", "WHEAT"]]
        # Care only pays together with a feed on the same day.
        if care and not tile.get("cared_today") and (tile.get("fed_today") or ["FEED"] in jobs):
            jobs.append(["CARE"])
        if tile.get("fertilizer_available"):
            if day <= 6:
                jobs.insert(0, ["COLLECT_FERTILIZER"])
            else:
                jobs.append(["COLLECT_FERTILIZER"])
        if tile.get("yield_units", 0) > 0:
            if day <= 6:
                jobs.insert(0, ["HARVEST"])   # wool and milk fund the second land
            else:
                jobs.append(["HARVEST"])
        return jobs
    if kind in {"COOP", "PASTURE"}:
        if ":" in label and label.split(":")[0] == kind:
            animal = label.split(":")[1]
            if inventory.get(animal, 0) > 0:
                return [["PLACE", animal]]
            return [["NEED", animal]] if stock.get(animal, 0) > 0 else []
        return [["DIG"]] if label != kind else []
    return []

def _worker_rank(tile, day, hour, prices):
    if not isinstance(tile, dict):
        return (5, 0)
    if tile.get("kind") == "PLANT":
        urgent = not tile.get("watered_today") and tile.get("consecutive_unwatered", 0) >= 1
        return (0 if urgent else 2, -prices.get(tile["crop"], 1))
    animal = tile.get("animal")
    if animal:
        urgent = not tile.get("fed_today") and tile.get("consecutive_unfed", 0) >= 1
        return (0 if urgent else 1 if hour <= 5 else 3, -prices.get(_WORKER_PRODUCTS[animal], 1))
    return (4, 0)

def _worker_assign(cells, desired, tiles, positions, blocks, day, size, basic, pinned):
    number = len(positions)
    owners = {cell: unit for unit, cell in enumerate(pinned) if cell in cells}
    available = set(cells) - set(owners)
    groups = []
    for block in blocks:
        group = sorted(set(block.get("cells", ())) & available)
        if group:
            groups.append(group)
            available.difference_update(group)
    for cell in sorted(available):
        if groups:
            group = min(groups, key=lambda part: min(_worker_distance(cell, other, size) for other in part))
            if min(_worker_distance(cell, other, size) for other in group) <= 2:
                group.append(cell)
                continue
        groups.append([cell])
    chunks = []
    width = max(1, (len(cells) + number - 1) // number)
    for group in groups:
        pending = set(group)
        while pending:
            cell = min(pending)
            chunk = []
            while pending and len(chunk) < width:
                cell = min(pending, key=lambda other: (_worker_distance(cell, other, size), other))
                chunk.append(cell)
                pending.remove(cell)
            chunks.append(chunk)
    def cost(cell):
        return len(_worker_plan(tiles[cell], desired.get(cell, "EMPTY"), day, 0,
            {"WHEAT": 1, "FERTILIZER": 0, "GOOSE": 1, "COW": 1, "SHEEP": 1},
            {"WHEAT": 1, "GOOSE": 1, "COW": 1, "SHEEP": 1},
            dict.fromkeys(_WORKER_CROPS, 1), basic))
    loads = [sum(cost(cell) for cell, owner in owners.items() if owner == unit) for unit in range(number)]
    centers = positions[:]
    for group in sorted(chunks, key=lambda part: (-sum(cost(cell) for cell in part), min(part))):
        work = sum(cost(cell) for cell in group)
        unit = min(range(number), key=lambda u: (loads[u] + work +
            min(_worker_distance(centers[u], cell, size) for cell in group), u))
        loads[unit] += work + min(_worker_distance(centers[unit], cell, size) for cell in group)
        centers[unit] = min(group, key=lambda cell: _worker_distance(centers[unit], cell, size))
        owners.update(dict.fromkeys(group, unit))
    return owners

def _route_jobs(tile, label, day, hour, inventory, stock, seeds, basic=False):
    if isinstance(tile, dict) and tile.get("animal"):
        animal = tile["animal"]
        release = label == "EMPTY" or label in _WORKER_CROPS or animal == "SHEEP" and day >= 28
        feed, care = (False, False) if release else _animal_service(tile, day)
        feed |= day < 27 and not release and tile.get("consecutive_unfed", 0) >= 1
        jobs = []
        missing_feed = feed and not tile.get("fed_today") and not inventory.get("WHEAT", 0)
        if feed and not tile.get("fed_today") and (inventory.get("WHEAT", 0) or stock.get("WHEAT", 0)):
            jobs.append(["FEED"] if inventory.get("WHEAT", 0) else ["NEED", "WHEAT"])
        if care and not tile.get("cared_today") and (tile.get("fed_today") or ["FEED"] in jobs):
            jobs.append(["CARE"])
        # Eggs are left on the goose until tonight's would not fit: one harvest turn for four eggs, not for two.
        full = animal != "GOOSE" or release or day >= 27 or tile.get("yield_units", 0) + 1 + tile.get("pending_care_bonus", 0) > 4
        if tile.get("yield_units", 0) > 0 and full:
            jobs.append(["HARVEST"])
        if tile.get("fertilizer_available"):
            jobs.append(["COLLECT_FERTILIZER"])
        if missing_feed and not jobs:
            jobs.append(["NEED", "WHEAT"])
        return jobs
    jobs = _worker_plan(tile, label, day, hour, inventory, stock, seeds, basic)
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today") and tile.get("consecutive_unwatered", 0) >= 1:
        remaining = (23 if day == 29 else 24) - hour
        if remaining == 1 and (["WATER"] in jobs or _WORKER_CROPS[tile["crop"]][3] and ["HARVEST"] in jobs):
            return [["WATER"]]
        if ["WATER"] in jobs:
            jobs.remove(["WATER"])
            if ["FERTILIZE"] in jobs:
                jobs.remove(["FERTILIZE"])
                jobs[:0] = [["FERTILIZE"], ["WATER"]]
            else:
                jobs.insert(0, ["WATER"])
    return jobs


def _day_routes(obs, state, desired, positions, inventories, tiles, stock, seeds):
    day, hour, size = obs["day"], obs["hour"], len(obs["farms"][obs["player"]]["tiles"])
    remaining = (23 if day == 29 else 24) - hour
    centers = (44, 45, 54, 55)
    prices = obs["market"]["prices"]
    fake = dict.fromkeys(("WHEAT", "GOOSE", "COW", "SHEEP"), 100)
    if stock.get("FERTILIZER", 0) + sum(inv.get("FERTILIZER", 0) for inv in inventories) > 0:
        fake["FERTILIZER"] = 1
    ready_seeds = dict.fromkeys(_WORKER_CROPS, 100)
    ready_stock = dict(fake)
    records = {}
    for cell, label in desired.items():
        tile = tiles[cell]
        jobs = _route_jobs(tile, label, day, hour, fake, ready_stock, ready_seeds)
        if not jobs:
            continue
        work = len(jobs)
        if isinstance(tile, dict) and tile.get("kind") == "PLANT" and _WORKER_CROPS[tile["crop"]][3] and day - tile["planted_day"] >= _WORKER_CROPS[tile["crop"]][1] and ["HARVEST"] in jobs:
            work += 1  # Harvest the remaining output and DIG before the next missed refresh.
        if tile is None and ":" in label:
            animal = label.split(":")[1]
            feed, care = _animal_service({"animal": animal, "placed_day": day}, day)
            work += 1 + feed + care  # BUILD, then PLACE and first service on this visit.
        elif isinstance(tile, dict) and tile.get("kind") == "WEED" and label in _WORKER_CROPS:
            work += 2
        elif isinstance(tile, dict) and tile.get("kind") == "PLANT" and ["HARVEST"] in jobs and not _WORKER_CROPS[tile["crop"]][3]:
            work += 2 if label in _WORKER_CROPS else 4 if ":" in label else 0
        dry = isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today") and tile.get("consecutive_unwatered", 0) >= 1
        urgent = (isinstance(tile, dict) and ((hour >= 10 and tile.get("kind") == "PLANT" and not tile.get("watered_today")
                  and tile.get("consecutive_unwatered", 0) >= 1)
                  or (_expiring(tile, day * 24 + hour - 16) and ["HARVEST"] in jobs)
                  or (tile.get("animal") and not tile.get("fed_today") and tile.get("consecutive_unfed", 0) >= 1 and ["FEED"] in jobs)))
        service = any(j[0] in ("FEED", "CARE", "COLLECT_FERTILIZER") for j in jobs)
        productive = tile is None or any(j[0] in ("HARVEST", "PLACE", "DIG") for j in jobs)
        rotting = isinstance(tile, dict) and _expiring(tile, day * 24 + hour) and ["HARVEST"] in jobs
        plantable = tile is None and jobs[0][0] == "PLANT" or (
            isinstance(tile, dict) and tile.get("kind") == "PLANT" and _WORKER_CROPS[tile["crop"]][3] and ["FERTILIZE"] in jobs)
        priority = 0 if urgent else 1 if service or rotting or plantable else 2 if dry else 3 if productive or ["WATER"] in jobs else 5
        item = tile.get("crop") or _WORKER_PRODUCTS.get(tile.get("animal"), "WHEAT") if isinstance(tile, dict) else label
        value = prices.get(item, prices.get(label, 1)) * (tile.get("yield_units", 1) if isinstance(tile, dict) else 3)
        records[cell] = {"turns": work, "priority": priority, "value": value}
    routes = [[] for _ in positions]
    pins = {cell: unit for cell, unit in state.get("_route_pins", {}).items() if cell in records and unit < len(positions)}
    for unit, cell in enumerate(state.get("_worker_targets", [])):
        if unit < len(positions) and cell in records and positions[unit] == cell:
            pins[cell] = unit
    for unit, old_route in enumerate(state.get("_day_routes", [])):
        if unit >= len(inventories):
            continue
        feed = inventories[unit].get("WHEAT", 0)
        animals = Counter({item: inventories[unit].get(item, 0) for item in ANIMAL_COST})
        for cell in old_route:
            if cell not in records or cell in pins:
                continue
            tile, label = tiles[cell], desired[cell]
            if isinstance(tile, dict) and tile.get("animal") and feed > 0 and ["FEED"] in _route_jobs(tile, label, day, hour, fake, ready_stock, ready_seeds):
                pins[cell] = unit
                feed -= 1
            elif ":" in label and not (isinstance(tile, dict) and tile.get("animal")):
                animal = label.split(":")[1]
                if animals[animal] > 0:
                    pins[cell] = unit
                    animals[animal] -= 1
    for cell, unit in sorted(pins.items(), key=lambda pair: (records[pair[0]]["priority"], pair[0])):
        routes[unit].append(cell)
    distance = _worker_distance
    def needs(route):
        items = Counter()
        for cell in route:
            tile, label = tiles[cell], desired[cell]
            if isinstance(tile, dict) and tile.get("animal"):
                if ["FEED"] in _route_jobs(tile, label, day, hour, fake, ready_stock, ready_seeds):
                    items["WHEAT"] += 1
            elif ":" in label and not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
                animal = label.split(":")[1]
                items[animal] += 1
                items["WHEAT"] += _animal_service({"animal": animal, "placed_day": day}, day)[0]
        return items
    def cost(unit, route):
        point = positions[unit]
        missing = [item for item, amount in needs(route).items() if amount > inventories[unit].get(item, 0)]
        walk, pickups = 0, len(missing)
        if missing and route:
            shed = min(centers, key=lambda c: (distance(point, c, size) + distance(c, route[0], size), c))
            walk += distance(point, shed, size)
            point = shed
        for cell in route:
            walk += distance(point, cell, size)
            point = cell
        terminal = day == 29 and bool(route or any(inventories[unit].values()))
        if terminal:
            walk += min(distance(point, c, size) for c in centers)
        return walk, walk + pickups + sum(records[cell]["turns"] for cell in route) + terminal
    def insertions(route, cell):
        rank = records[cell]["priority"]
        return [i for i in range(len(route) + 1) if (i == 0 or records[route[i - 1]]["priority"] <= rank)
                and (i == len(route) or rank <= records[route[i]]["priority"])]
    pending = []
    for cell in sorted(set(records) - set(pins), key=lambda c: (records[c]["priority"], -records[c]["value"], c)):
        options = []
        for unit, route in enumerate(routes):
            old_walk, _ = cost(unit, route)
            for i in insertions(route, cell):
                candidate = route[:i] + [cell] + route[i:]
                walk, turns = cost(unit, candidate)
                if turns <= remaining or records[cell]["priority"] == 0 and not route:
                    options.append((max(0, turns - remaining), walk - old_walk + .35 * turns, unit, i))
        if not options:
            pending.append(cell)
            continue
        _, _, unit, i = min(options)
        routes[unit].insert(i, cell)
    # honey: bounded local search for at most 100 cells; reconsider if board size grows.
    for _ in range(2):
        improved = False
        for left, route in enumerate(routes):
            for cell in list(route):
                if cell in pins:
                    continue
                old_walk, _ = cost(left, route)
                shorter = [c for c in route if c != cell]
                short_walk, _ = cost(left, shorter)
                best = None
                for right, other in enumerate(routes):
                    if left == right:
                        continue
                    other_walk, _ = cost(right, other)
                    for i in insertions(other, cell):
                        longer = other[:i] + [cell] + other[i:]
                        walk, turns = cost(right, longer)
                        gain = old_walk + other_walk - short_walk - walk
                        if gain > 0 and turns <= remaining and (best is None or gain > best[0]):
                            best = (gain, right, longer)
                    for i, swap in enumerate(other):
                        if swap in pins or records[swap]["priority"] != records[cell]["priority"]:
                            continue
                        one = [swap if c == cell else c for c in route]
                        two = [cell if c == swap else c for c in other]
                        w1, t1 = cost(left, one)
                        w2, t2 = cost(right, two)
                        gain = old_walk + other_walk - w1 - w2
                        if gain > 0 and max(t1, t2) <= remaining and (best is None or gain > best[0]):
                            best = (gain, right, two, one)
                if best:
                    routes[left] = best[3] if len(best) == 4 else shorter
                    routes[best[1]] = best[2]
                    route = routes[left]
                    improved = True
        if not improved:
            break
    state["_route_jobs"] = records
    state["_route_pending"] = pending
    state["_route_estimates"] = [cost(u, route)[1] for u, route in enumerate(routes)]
    return routes


def _day_worker_actions(obs, state, desired):
    farm, private = obs["farms"][obs["player"]], obs["private"]
    size, day, hour = len(farm["tiles"]), obs["day"], obs["hour"]
    remaining = (23 if day == 29 else 24) - hour
    positions = [y * size + x for x, y in [farm["farmer"], *farm["hands"]]]
    inventories = [dict(inv) for inv in private["inventories"]]
    tiles = [tile for row in farm["tiles"] for tile in row]
    stock, seeds = dict(private["shed"]), dict(private["seeds"])
    seeds["_CASH"] = farm["money"]
    centers = (44, 45, 54, 55)
    key = (day, tuple(farm["unlocked_quadrants"]), tuple(obs["town"]["unlocked_shops"]), len(positions), (hour >= 10) + (hour >= 14) + (hour >= 18))
    supply = {**{"seed:" + k: n for k, n in seeds.items() if k != "_CASH"}, **stock}
    arrived = any(n > state.get("_route_supply", {}).get(item, 0) for item, n in supply.items())
    state.setdefault("_route_pins", {})
    if state.get("_route_key", (None,))[0] != day:
        state["_route_pins"] = {}
        state["_worker_targets"] = []
    if state.get("_route_key") != key or arrived:
        state["_day_routes"] = _day_routes(obs, state, desired, positions, inventories, tiles, stock, seeds)
        state["_route_key"] = key
    state["_route_supply"] = supply
    routes = state["_day_routes"]
    owners = {cell: unit for unit, route in enumerate(routes) for cell in route}
    state["fertilizer_need"] = sum(_worker_fert_eligible(t, day) for t in tiles)
    pending = state.get("pending_purchases", {})
    prices = obs["market"]["prices"]
    cash_short = farm["money"] < sum(n * _ITEM_COST.get(item, 40) for category in ("seed", "animal", "feed")
                                   for item, n in pending.get(category, {}).items())
    actions = []
    served = set()
    # From hour 16, whatever dies tonight is handed to the nearest worker that can still reach it,
    # farthest cells first. This overrides the routes.
    forced = {}
    if hour >= 16 and day < 29:
        def reach(worker, cell):
            point = positions[worker]
            if tiles[cell].get("animal") and not inventories[worker].get("WHEAT", 0):
                if not stock.get("WHEAT", 0):
                    return 1000
                return min(_worker_distance(point, c, size) + _worker_distance(c, cell, size) + 2 for c in centers)
            return _worker_distance(point, cell, size) + 1
        must = []
        for cell, label in desired.items():
            tile = tiles[cell]
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                spent = _WORKER_CROPS[tile["crop"]][3] and day - tile["planted_day"] >= _WORKER_CROPS[tile["crop"]][1]
                if not tile.get("watered_today") and tile.get("consecutive_unwatered", 0) >= 1 and label != "EMPTY" and not spent:
                    must.append(cell)
            elif (tile.get("animal") and not tile.get("fed_today") and tile.get("consecutive_unfed", 0) >= 1 and day < 27
                  and label not in {"EMPTY", *_WORKER_CROPS}):
                must.append(cell)
        free = set(range(len(positions)))
        # A worker already standing on such a cell serves it; yesterday's hand-out is kept, so nobody turns back.
        kept = state.get("_forced", {}) if state.get("_forced_day") == day else {}
        for worker in sorted(free):
            cell = positions[worker] if positions[worker] in must and reach(worker, positions[worker]) == 1 else kept.get(worker)
            if cell in must and cell not in forced.values() and reach(worker, cell) <= remaining:
                forced[worker] = cell
        free -= set(forced)
        for cell in sorted(set(must) - set(forced.values()), key=lambda c: (-min([reach(u, c) for u in free] or [0]), c)):
            able = [u for u in free if reach(u, cell) <= remaining]
            if able:
                worker = min(able, key=lambda u: (reach(u, cell), u))
                forced[worker] = cell
                free.discard(worker)
        served.update(forced.values())
    state["_forced"], state["_forced_day"] = forced, day
    for unit, position in enumerate(positions):
        inventory, route = inventories[unit], routes[unit]
        if unit in forced:
            cell = forced[unit]
            if tiles[cell].get("animal") and not inventory.get("WHEAT", 0):
                shed = min(centers, key=lambda c: (_worker_distance(position, c, size) + _worker_distance(c, cell, size), c))
                if position == shed:
                    action = ["PICKUP", "WHEAT", 1]
                    stock["WHEAT"] -= 1
                else:
                    action = _worker_move(position, shed, size)
            elif position != cell:
                action = _worker_move(position, cell, size)
            else:
                action = ["FEED"] if tiles[cell].get("animal") else ["WATER"]
            actions.append(action)
            continue
        def jobs(cell):
            return _route_jobs(tiles[cell], desired.get(cell, "EMPTY"), day, hour, inventory, stock, seeds)
        # Completed cells are released. Newly built/harvested cells keep their continuation.
        route[:] = [cell for cell in route if jobs(cell)]
        for cell, owner in list(owners.items()):
            if owner == unit and cell not in route:
                owners.pop(cell)
        for cell, owner in list(state["_route_pins"].items()):
            if owner == unit and not jobs(cell):
                state["_route_pins"].pop(cell)
        if hour >= 10:
            def rescue_turns(worker, cell):
                tile, point = tiles[cell], positions[worker]
                if tile.get("animal") and not inventories[worker].get("WHEAT", 0):
                    if not stock.get("WHEAT", 0):
                        return 1000
                    return min(_worker_distance(point, c, size) + _worker_distance(c, cell, size) + 2 for c in centers)
                return _worker_distance(point, cell, size) + 1
            urgent = []
            for cell, label in desired.items():
                tile = tiles[cell]
                if cell in served or not isinstance(tile, dict):
                    continue
                plant = hour >= 10 and day < 29 and tile.get("kind") == "PLANT" and not tile.get("watered_today") and tile.get("consecutive_unwatered", 0) >= 1
                animal = tile.get("animal") and not tile.get("fed_today") and tile.get("consecutive_unfed", 0) >= 1 and day < 27
                rotting = _expiring(tile, day * 24 + hour - 16)
                if not (plant or animal or rotting):
                    continue
                owner = owners.get(cell, state["_route_pins"].get(cell))
                turns = rescue_turns(unit, cell)
                if turns <= remaining and (owner in (None, unit) or turns < rescue_turns(owner, cell)):
                    urgent.append(cell)
            if urgent:
                cell = min(urgent, key=lambda c: (any(rescue_turns(other, c) < rescue_turns(unit, c) for other in range(len(positions)) if other != unit),
                                                  rescue_turns(unit, c), c))
                previous = owners.get(cell)
                if previous is not None and previous != unit:
                    routes[previous].remove(cell)
                if cell in route:
                    route.remove(cell)
                route.insert(0, cell)
                owners[cell] = unit
                state["_route_pins"][cell] = unit
        if not route:
            candidates = [cell for cell in state.get("_route_pending", []) if cell not in owners and jobs(cell)
                          and _worker_distance(position, cell, size) + state["_route_jobs"][cell]["turns"] <= remaining]
            if candidates:
                cell = min(candidates, key=lambda c: (state["_route_jobs"][c]["priority"],
                    _worker_distance(position, c, size), -state["_route_jobs"][c]["value"], c))
                route.append(cell)
                owners[cell] = unit
                state["_route_pending"].remove(cell)
        if inventory.get("FERTILIZER", 0) and not (route and _expiring(tiles[route[0]], day * 24 + hour - 16)):
            taken = state.setdefault("_fert_targets", {})
            if taken.get("_step") != (day, hour):
                taken.clear(); taken["_step"] = (day, hour)
            eligible = [cell for cell in desired if cell not in route and cell not in taken
                        and (owners.get(cell, unit) == unit or _worker_distance(position, cell, size) <= 4)
                        and _worker_fert_eligible(tiles[cell], day)
                        and _worker_distance(position, cell, size) + 2 <= remaining]
            if eligible:
                cell = min(eligible, key=lambda c: (_worker_distance(position, c, size), c))
                if _worker_distance(position, cell, size) <= 2:
                    route.insert(0, cell)   # on the way: use it now
                else:
                    route.append(cell)
                owners[cell] = unit
                taken[cell] = unit
        need = Counter()
        for cell in route:
            tile, label = tiles[cell], desired.get(cell, "EMPTY")
            if isinstance(tile, dict) and tile.get("animal"):
                if not tile.get("fed_today") and (_animal_service(tile, day)[0] or day < 27 and tile.get("consecutive_unfed", 0) >= 1) and label not in {"EMPTY", *_WORKER_CROPS}:
                    need["WHEAT"] += 1
            elif ":" in label and not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
                animal = label.split(":")[1]
                need[animal] += 1
                need["WHEAT"] += _animal_service({"animal": animal, "placed_day": day}, day)[0]
        need["FERTILIZER"] = sum(_worker_fert_eligible(tiles[cell], day) for cell in route)
        available = [(cell, jobs(cell)) for cell in route]
        target = route[0] if route else None
        head = tiles[target] if target is not None else None
        urgent_plant = day < 29 and isinstance(head, dict) and head.get("kind") == "PLANT" and not head.get("watered_today") and head.get("consecutive_unwatered", 0) >= 1
        urgent_animal = isinstance(head, dict) and head.get("animal") and not head.get("fed_today") and head.get("consecutive_unfed", 0) >= 1 and day < 27
        urgent_crop = _expiring(head, day * 24 + hour - 16)
        urgent_ready = urgent_crop or urgent_plant or urgent_animal and (inventory.get("WHEAT", 0) or stock.get("WHEAT", 0))
        if urgent_ready:
            turns = _worker_distance(position, target, size) + 1
            if urgent_animal and not inventory.get("WHEAT", 0):
                turns = min(_worker_distance(position, c, size) + _worker_distance(c, target, size) + 2 for c in centers)
            urgent_ready = turns <= remaining
        immediate = next((j[0] for cell, j in available if cell == position and j[0][0] != "NEED" and position not in served), None)
        here = tiles[position]
        dry_here = (day < 29 and position not in served and isinstance(here, dict) and here.get("kind") == "PLANT"
                    and not here.get("watered_today") and here.get("consecutive_unwatered", 0) >= 1
                    and not (_WORKER_CROPS[here["crop"]][3] and day - here["planted_day"] >= _WORKER_CROPS[here["crop"]][1]))
        visit = (jobs(position) if position in desired and position not in served and isinstance(here, dict)
                 and here.get("animal") else [])
        if dry_here:
            action = immediate if immediate == ["FERTILIZE"] and remaining >= 2 else ["WATER"]
        elif visit and visit[0][0] != "NEED":
            action = visit[0]
        elif urgent_ready:
            if urgent_animal and not inventory.get("WHEAT", 0):
                shed = min(centers, key=lambda c: (_worker_distance(position, c, size) + _worker_distance(c, target, size), c))
                if position == shed:
                    quantity = min(stock["WHEAT"], max(1, need["WHEAT"]))
                    action = ["PICKUP", "WHEAT", quantity]
                    stock["WHEAT"] -= quantity
                else:
                    action = _worker_move(position, shed, size)
            elif position != target:
                action = _worker_move(position, target, size)
            elif urgent_animal:
                action = ["FEED"]
            elif urgent_crop and (not urgent_plant or not _WORKER_CROPS[head["crop"]][3]):
                action = ["HARVEST"]
            else:
                action = jobs(target)[0] if remaining > 1 else ["WATER"]
        elif immediate is not None:
            action = immediate
        else:
            supplies = [(item, max(0, n - inventory.get(item, 0))) for item, n in need.items()]
            supplies = [(item, min(n, stock.get(item, 0))) for item, n in supplies if n > 0 and stock.get(item, 0) > 0]
            target = route[0] if route else None
            shed = min(centers, key=lambda c: (_worker_distance(position, c, size) +
                       (_worker_distance(c, target, size) if target is not None else 0), c))
            products = {item: n for item, n in inventory.items() if n > 0 and item not in ANIMAL_COST
                        and (item != "WHEAT" or n > need["WHEAT"])
                        and (item != "FERTILIZER" or not any(_worker_fert_eligible(tiles[c], day) for c in route))}
            sellable = bool(products)
            if position in centers and sellable and remaining > 2:
                item = max(products, key=lambda k: (prices.get(k, 1) * products[k], k))
                room = max(0, 100 - sum(stock.values()))
                quantity = min(room, products[item] - (need["WHEAT"] if item == "WHEAT" else 0))
                action = ["PLACE", item, quantity] if quantity else ["PASS"]
                stock[item] = stock.get(item, 0) + quantity
            elif sellable and (cash_short or sum(products.values()) >= 8
                               or hour >= 20
                               or day == 29 and (not route or remaining <= _worker_distance(position, shed, size) + 2)):
                if position == shed:
                    room = max(0, 100 - sum(stock.values()))
                    reserved = any(inventory.get(item, 0) and n for item, n in need.items()) or inventory.get("FERTILIZER", 0) and any(_worker_fert_eligible(tiles[c], day) for c in route)
                    if sum(inventory.values()) <= room and not reserved:
                        action = ["DROP"]
                        for item, n in inventory.items():
                            stock[item] = stock.get(item, 0) + n
                    else:
                        item = max(products, key=lambda k: (prices.get(k, 1) * products[k], k))
                        quantity = min(room, products[item] - (need["WHEAT"] if item == "WHEAT" else 0))
                        action = ["PLACE", item, quantity] if quantity else ["PASS"]
                        stock[item] = stock.get(item, 0) + quantity
                else:
                    action = _worker_move(position, shed, size)
            elif supplies and (position in centers or not available or available[0][1][0][0] == "NEED"):
                if position == shed:
                    item, quantity = supplies[0]
                    action = ["PICKUP", item, quantity]
                    stock[item] -= quantity
                else:
                    action = _worker_move(position, shed, size)
            else:
                feasible = [cell for cell, j in available if j[0][0] != "NEED"
                            and _worker_distance(position, cell, size) + (2 if j[0][0] == "PLANT" else 1) <= remaining]
                if feasible:
                    target = feasible[0]
                    action = jobs(target)[0] if position == target else _worker_move(position, target, size)
                else:
                    action = ["PASS"]
        if action[0] == "PLANT":
            seeds[action[1]] -= 1
        if action[0] in {"PLANT", "WATER", "FERTILIZE", "HARVEST", "FEED", "CARE", "COLLECT_FERTILIZER", "BUILD_COOP", "BUILD_PASTURE", "DIG"} or action[0] == "PLACE" and position in route:
            state["_route_pins"][position] = unit
            served.add(position)
        if action[0] in {"NORTH", "SOUTH", "EAST", "WEST", "PICKUP"} and target is not None:
            served.add(target)  # Later workers must not invalidate an already emitted route action.
        actions.append(action)
    state["_worker_targets"] = [route[0] if route else None for route in routes]
    state["_worker_owners"] = owners
    state["_worker_areas"] = [list(route) for route in routes]
    return actions


# Weights of the next-cell choice, fitted to 44,930 recorded choices of the reference team (days 12-23).
# Each option's score is the sum of weight x fact; the worker takes the best-scoring cell it can still finish.
_CHOICE_W = [-0.880, 1.327, 0.085, -0.235, 0.367, 0.731, 0.287, 0.194, 0.412, -2.163, 0.241, -1.039, -0.143, -1.076, -0.086,
             2.791, 1.434, 5.589, -0.364, 0.872, -0.116, 0.182, 0.368, 1.338, -0.503, 1.312, -0.565, 0.000, 0.766, -1.250,
             0.371, 0.400, 0.128, -1.218, 0.989, -1.035, 0.160]
_FERT_PULL = 3.0    # worth of a strawberry or tomato that can take the fertilizer in hand, in score points (about 3 steps)
_DEADLINE_MARGIN = 3   # spare turns kept when judging whether a worker can still reach its deadline cells
import os as _os_end
# End-of-day losses (idea from the 5th-place write-up and its MIT-licensed code): bit 1, on the last day the walk
# home comes before any job once time is short; bit 2, when the crew's loads alone would overflow the shed at
# midnight, the most loaded workers near the shed bring theirs in during the last hours.
_END = int(_os_end.environ.get('END', 3))
_CHOICE_ONGOING = {"STRAWBERRY": (10, 2, 16), "TOMATO": (8, 1, 11)}

def _choice_needs(tile, day):
    """What a cell offers, as indexes into _CHOICE_W (the same facts the weights were fitted on)."""
    if tile is None:
        return (10,)
    if not isinstance(tile, dict):
        return ()
    if tile.get("kind") == "WEED":
        return (10,)
    if tile.get("animal"):
        out = []
        if not tile.get("fed_today"):
            out.append(3)
            if tile.get("consecutive_unfed", 0) >= 1:
                out.append(21)
        elif not tile.get("cared_today"):
            out.append(24)
        if tile.get("yield_units", 0) > 0 or tile.get("fertilizer_available"):
            out.append(4)
        return tuple(out)
    if tile.get("kind") != "PLANT":
        return ()
    crop, age, watered, out = tile["crop"], day - tile["planted_day"], bool(tile.get("watered_today")), []
    if not watered and tile.get("consecutive_unwatered", 0) >= 1:
        out.append(5)
    if crop in _CHOICE_ONGOING:
        first, gap, last = _CHOICE_ONGOING[crop]
        if not watered and first <= age + 1 <= last and (age + 1 - first) % gap == 0:
            out.append(6)
        if tile.get("yield_units", 0) > 0:
            out.append(8)
    elif tile.get("yield_units", 0) > 0 and age >= _FIRST[crop]:
        out.append(7)
    if not watered and not out:
        out.append(9)
    return tuple(out)

def _block_worker_actions(obs, state, desired):
    """Day planner by blocks. The farm is cut into one compact block per worker, each with about the
    same amount of today's work. A worker takes the nearest cell of its block that needs work and
    finishes it before leaving; with nothing left in its block it helps on the nearest open cell.
    It crosses the farm only for the shed, for something that dies tonight, or to help."""
    farm, private = obs["farms"][obs["player"]], obs["private"]
    size, day, hour = len(farm["tiles"]), obs["day"], obs["hour"]
    remaining = (23 if day == 29 else 24) - hour
    positions = [y * size + x for x, y in [farm["farmer"], *farm["hands"]]]
    inventories = [dict(inv) for inv in private["inventories"]]
    tiles = [tile for row in farm["tiles"] for tile in row]
    stock, seeds = dict(private["shed"]), dict(private["seeds"])
    seeds["_CASH"] = farm["money"]
    centers = (44, 45, 54, 55)
    number = len(positions)
    planned = max(number, 1 + TEMPLATE["hands"][min(29, day)])
    lands = [q for q in ("NW", "NE", "SE", "SW") if q in farm["unlocked_quadrants"]]
    if state.get("_live_day") != day:
        state["_live_day"], state["_claims"], state["_forced"], state["_targets"] = day, {}, {}, {}
    claims = {cell: unit for cell, unit in state["_claims"].items() if unit < number}
    def dist(a, b):
        return _worker_distance(a, b, size)
    def to_shed(cell):
        return min(dist(cell, c) for c in centers)
    full = {"WHEAT": 9, "FERTILIZER": 1, "GOOSE": 1, "COW": 1, "SHEEP": 1}
    all_seeds = {**dict.fromkeys(_WORKER_CROPS, 9), "_CASH": 10 ** 9}
    def work(cell):
        plan = _route_jobs(tiles[cell], desired.get(cell, "EMPTY"), day, hour, full,
                           {**stock, "WHEAT": 9, "GOOSE": 1, "COW": 1, "SHEEP": 1}, all_seeds)
        tile = tiles[cell]
        replant = (["HARVEST"] in plan and isinstance(tile, dict) and tile.get("kind") == "PLANT"
                   and not _WORKER_CROPS[tile["crop"]][3])
        return plan + [["PLANT"], ["WATER"]] * replant
    # Blocks: slices around the shed, cut where the day's work is evenly shared. Fixed for the day.
    half = size // 2
    if state.get("_strip_key") != (day, planned, len(lands)):
        owned = [cell for cell in range(size * size) if tiles[cell] != "LOCKED"]
        path = sorted(owned, key=lambda cell: (math.atan2(cell // size - (size - 1) / 2, cell % size - (size - 1) / 2), cell))
        weight = [0.4 + len(work(cell)) if cell in desired else 0.0 for cell in path]
        total, running, cut = sum(weight) or 1.0, 0.0, [set() for _ in range(planned)]
        for cell, w in zip(path, weight):
            cut[min(planned - 1, int(running / total * planned))].add(cell)
            running += w
        state["_strips"], state["_strip_key"], state["_slice_of"] = cut, (day, planned, len(lands)), {}
    slice_of = state.setdefault("_slice_of", {})
    for unit in range(number):
        if unit not in slice_of:
            free = [k for k in range(len(state["_strips"])) if k not in slice_of.values()]
            if free:
                slice_of[unit] = min(free, key=lambda k: (min([dist(positions[unit], c) for c in state["_strips"][k]] or [99]), k))
    strips = [state["_strips"][slice_of[unit]] if unit in slice_of else set() for unit in range(number)]
    state["fertilizer_need"] = sum(_worker_fert_eligible(t, day) for t in tiles)
    prices = obs["market"]["prices"]
    def dying(cell):
        tile, label = tiles[cell], desired.get(cell, "EMPTY")
        if not isinstance(tile, dict):
            return False
        if tile.get("kind") == "PLANT":
            spent = _WORKER_CROPS[tile["crop"]][3] and day - tile["planted_day"] >= _WORKER_CROPS[tile["crop"]][1]
            return (day < 29 and not tile.get("watered_today") and tile.get("consecutive_unwatered", 0) >= 1
                    and label != "EMPTY" and not spent)
        return bool(tile.get("animal") and not tile.get("fed_today") and tile.get("consecutive_unfed", 0) >= 1
                    and day < 27 and label not in {"EMPTY", *_WORKER_CROPS})
    def reach(worker, cell):
        point = positions[worker]
        if tiles[cell].get("animal") and not inventories[worker].get("WHEAT", 0):
            if not stock.get("WHEAT", 0):
                return 1000
            return min(dist(point, c) + dist(c, cell) + 2 for c in centers)
        return dist(point, cell) + 1
    # Last resort from hour 18: whatever still dies tonight goes to the nearest worker that can reach it.
    forced = {}
    # From hour 16 a cell that dies tonight is given to a worker at most three steps away (a short detour,
    # never a march across the farm); from hour 20 to the nearest worker that can still reach it.
    limit = remaining
    # An animal on its second hungry day needs a feed fetched from the shed, which takes longer than a walk
    # to a plant: it is handed out from hour 14. A plant that dies tonight is handed out from hour 20.
    if hour >= 14:
        must = [cell for cell in desired if dying(cell)
                and (hour >= 20 or bool(isinstance(tiles[cell], dict) and tiles[cell].get("animal")))]
        free = set(range(number))
        kept = state.get("_forced", {})
        for worker in sorted(free):
            cell = positions[worker] if positions[worker] in must and reach(worker, positions[worker]) == 1 else kept.get(worker)
            if cell in must and cell not in forced.values() and reach(worker, cell) <= min(limit, remaining):
                forced[worker] = cell
        free -= set(forced)
        for cell in sorted(set(must) - set(forced.values()), key=lambda c: (-min([reach(u, c) for u in free] or [0]), c)):
            able = [u for u in free if reach(u, cell) <= min(limit, remaining)]
            if able:
                worker = min(able, key=lambda u: (reach(u, cell), u))
                forced[worker] = cell
                free.discard(worker)
        for worker, cell in forced.items():
            claims[cell] = worker
    state["_forced"] = forced
    actions, acted = [], set()
    if state.get("_last_worked_day") != day:
        state["_last_worked_day"], state["_last_worked"] = day, {}
    last_worked = state["_last_worked"]
    cell_needs = {cell: _choice_needs(tiles[cell], day) for cell in desired}
    needy = {cell for cell, facts in cell_needs.items() if facts}
    everything = set(desired)
    feed_out = [0]
    # The end goal first. Two kinds of cell cannot wait for tomorrow: a plant that dies tonight unless watered,
    # and fruit on its last day before it rots. Each belongs to the worker nearest to it. A worker does what
    # lies on its way only while it can still walk to all of its own and do them before midnight; once the time
    # left is down to that walk plus a small margin, they come before everything else, and nothing else is done
    # on the way (a picked plant is dug and replanted later).
    def last_pick(cell):
        tile = tiles[cell]
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("yield_units", 0) > 0):
            return False
        limit = tile.get("max_lifespan_step", -1)
        return 0 <= limit <= (day + 1) * 24 and day - tile["planted_day"] >= _WORKER_CROPS[tile["crop"]][0]
    def pays_tonight(cell):
        # a sheep or cow that produces tonight pays out its saved care bonus only if it is fed today
        tile = tiles[cell]
        if not (isinstance(tile, dict) and tile.get("animal") in ("SHEEP", "COW")) or tile.get("fed_today") or day >= 29:
            return False
        if tile.get("pending_care_bonus", 0) <= 0 or desired.get(cell, "EMPTY") in {"EMPTY", *_WORKER_CROPS}:
            return False
        first, interval, cap = _ANIMAL_RULES[tile["animal"]]
        since = day + 1 - tile.get("placed_day", day) - first
        return since >= 0 and since % interval == 0 and stock.get("WHEAT", 0) + sum(inv.get("WHEAT", 0) for inv in inventories) > 0
    due_cells = [c for c in desired if isinstance(tiles[c], dict)
                 and (tiles[c].get("kind") == "PLANT" and (dying(c) or last_pick(c)) or pays_tonight(c))]
    mine_due = [[] for _ in range(number)]
    for c in due_cells:
        mine_due[min(range(number), key=lambda v: (dist(positions[v], c), v))].append(c)
    must_now = set()
    for v in range(number):
        at, left, steps = positions[v], list(mine_due[v]), 0
        fetch = not inventories[v].get("WHEAT", 0) and any(tiles[c].get("animal") for c in left)
        if fetch:      # no feed in hand: the walk starts with a stop at the shed
            shed = min(centers, key=lambda c: (dist(at, c), c))
            steps += dist(at, shed) + 1
            at = shed
        while left:
            nxt = min(left, key=lambda c: (dist(at, c), c))
            steps += dist(at, nxt) + (2 if tiles[nxt].get("animal") else 1)
            at = nxt
            left.remove(nxt)
        if mine_due[v] and steps + _DEADLINE_MARGIN >= remaining:
            must_now.update(mine_due[v])
    def ripe_melon(cell):
        tile = tiles[cell]
        return (isinstance(tile, dict) and tile.get("crop") == "MELON" and day - tile["planted_day"] >= 10
                and tile.get("yield_units", 0) >= 5)
    def feed_left():
        hungry_all = sum(1 for c in desired if isinstance(tiles[c], dict) and tiles[c].get("animal") and not tiles[c].get("fed_today")
                         and ["FEED"] in _route_jobs(tiles[c], desired.get(c, "EMPTY"), day, hour, {"WHEAT": 1}, stock, seeds))
        return hungry_all - sum(inv.get("WHEAT", 0) for inv in inventories) - feed_out[0]
    couriers = set()
    if _END & 2 and day < 29 and hour >= 20:
        loads = [sum(n for k, n in inv.items() if k not in ANIMAL_COST) for inv in inventories]
        excess = sum(loads) - 90
        for v in sorted(range(number), key=lambda v: (to_shed(positions[v]) - loads[v] / 4, v)):
            if excess <= 0:
                break
            if loads[v] and not mine_due[v] and to_shed(positions[v]) < remaining:
                couriers.add(v)
                excess -= loads[v]
    def bring_in(position, inventory):
        shed = min(centers, key=lambda c: (dist(position, c), c))
        if position != shed:
            return _worker_move(position, shed, size)
        room = max(0, 100 - sum(stock.values()))
        goods = {k: n for k, n in inventory.items() if n > 0 and k not in ANIMAL_COST}
        if goods and sum(inventory.values()) <= room:
            for item, n in inventory.items():
                stock[item] = stock.get(item, 0) + n
            return ["DROP"]
        if goods and room > 0:
            item = max(goods, key=lambda k: (prices.get(k, 1) * min(room, goods[k]), k))
            stock[item] = stock.get(item, 0) + min(room, goods[item])
            return ["PLACE", item, min(room, goods[item])]
        return None
    for unit, position in enumerate(positions):
        # no fixed areas for the work itself: 'home' only sizes what a worker takes from the shed
        inventory = inventories[unit]
        homeward = None
        if _END & 1 and day == 29 and any(n for k, n in inventory.items() if k not in ANIMAL_COST):
            if remaining <= min(dist(position, c) for c in centers) + 2:
                homeward = bring_in(position, inventory)
        elif unit in couriers:
            homeward = bring_in(position, inventory)
        if homeward is not None:
            actions.append(homeward)
            continue
        inventory, home, block = inventories[unit], strips[unit] if unit < len(strips) else set(), everything
        # Fertilizer collected from an animal goes straight onto a plant, no shed trip. Strawberries and tomatoes
        # come first: wheat and carrots take it only when the crew holds more than those still need.
        ongoing_need = (sum(1 for c in block if _worker_fert_eligible(tiles[c], day) and _WORKER_CROPS[tiles[c]["crop"]][3])
                        - sum(inv.get("FERTILIZER", 0) for v, inv in enumerate(inventories) if v != unit))
        def jobs(cell):
            plan = _route_jobs(tiles[cell], desired.get(cell, "EMPTY"), day, hour, inventory, stock, seeds)
            tile = tiles[cell]
            if (["FERTILIZE"] in plan and isinstance(tile, dict) and tile.get("kind") == "PLANT"
                    and not _WORKER_CROPS[tile["crop"]][3] and inventory.get("FERTILIZER", 0) <= ongoing_need):
                plan = [job for job in plan if job != ["FERTILIZE"]]
            return plan
        def shed_for(cell):
            return min(centers, key=lambda c: (dist(position, c) + dist(c, cell), c))
        if unit in forced:
            cell = forced[unit]
            if tiles[cell].get("animal") and not inventory.get("WHEAT", 0):
                shed = shed_for(cell)
                if position == shed:
                    action = ["PICKUP", "WHEAT", 1]
                    stock["WHEAT"] -= 1
                else:
                    action = _worker_move(position, shed, size)
            elif position != cell:
                action = _worker_move(position, cell, size)
            else:
                action = ["FEED"] if tiles[cell].get("animal") else ["WATER"]
                acted.add(cell)
            actions.append(action)
            continue
        for cell in [c for c, owner in claims.items() if owner == unit]:
            if not jobs(cell):
                del claims[cell]
        action = None
        # 1. Finish the cell under the worker's feet: everything it needs today, in one visit.
        here = jobs(position) if position in desired and position not in acted else []
        if here and position not in must_now and any(c in must_now and c not in acted for c in mine_due[unit]):
            here = []      # its own deadline cells are waiting: nothing extra is done on the way
        if inventory.get("MELON", 0) > 0 and tiles[position] is None and hour < 21:
            here = []      # melons in hand go to the shed first; the empty cell is replanted by whoever comes next
        owner = claims.get(position, unit)
        if here and position not in block and state["_targets"].get(unit) != position:
            pressing = dying(position) or _expiring(tiles[position], day * 24 + hour - 16)
            if not pressing and any(c not in acted and claims.get(c, unit) == unit and jobs(c) for c in block):
                here = []
        if here and here[0][0] != "NEED" and (owner == unit or positions[owner] != position):
            claims[position] = unit
            action = here[0]
            acted.add(position)
        # 1b. Water in passing: a plant under the worker's feet that has had no water today is watered before
        #     moving on, due or not. Every plant then carries a day in hand, so a missed visit tomorrow is
        #     not a death and no worker has to march across the farm to save it.
        if action is None and day < 29 and position in desired and position not in acted:
            under = tiles[position]
            if (isinstance(under, dict) and under.get("kind") == "PLANT" and under.get("yield_units", 0) > 0
                    and _WORKER_CROPS[under["crop"]][3] and claims.get(position, unit) == unit):
                action = ["HARVEST"]      # fruit in passing: a strawberry or tomato holding fruit is picked by whoever stands on it
                acted.add(position)
            elif (False and isinstance(under, dict) and under.get("kind") == "PLANT" and not under.get("watered_today")
                    and desired.get(position) != "EMPTY" and claims.get(position, unit) == unit
                    and not (_WORKER_CROPS[under["crop"]][3] and day - under["planted_day"] >= _WORKER_CROPS[under["crop"]][1])):
                action = ["WATER"]
                acted.add(position)
        # 2. Standing at the shed: take what the block needs today (animals to place, feed, fertilizer),
        #    and leave what was harvested. No trips are made to the shed for a deposit.
        products = {item: n for item, n in inventory.items() if n > 0 and item not in ANIMAL_COST
                    and item not in ("WHEAT", "FERTILIZER")}
        surplus_wheat = max(0, inventory.get("WHEAT", 0) - 8)
        if action is None and position in centers:
            fed = {"WHEAT": 1}
            hungry = sum(1 for c in home if isinstance(tiles[c], dict) and tiles[c].get("animal") and not tiles[c].get("fed_today")
                         and ["FEED"] in _route_jobs(tiles[c], desired.get(c, "EMPTY"), day, hour, fed, stock, seeds))
            eligible = (sum(1 for c in home if _worker_fert_eligible(tiles[c], day))
                        - sum(1 for c in home if isinstance(tiles[c], dict) and tiles[c].get("fertilizer_available")))
            wanted_animal = next((desired[c].split(":")[1] for c in sorted(home, key=lambda c: (dist(position, c), c))
                                  if ":" in desired.get(c, "") and not (isinstance(tiles[c], dict) and (tiles[c].get("animal") or tiles[c].get("kind") == "PLANT"))
                                  and stock.get(desired[c].split(":")[1], 0) > 0
                                  and not inventory.get(desired[c].split(":")[1], 0)), None)
            room = max(0, 100 - sum(stock.values()))
            if (products or surplus_wheat) and remaining > 1 and room > 0:
                item = max(products, key=lambda k: (prices.get(k, 1) * products[k], k)) if products else "WHEAT"
                quantity = min(room, products[item] if products else surplus_wheat)
                action = ["PLACE", item, quantity]
                stock[item] = stock.get(item, 0) + quantity
            elif wanted_animal and not any(inventory.get(a, 0) for a in ANIMAL_COST):
                action = ["PICKUP", wanted_animal, 1]
                stock[wanted_animal] -= 1
            elif stock.get("WHEAT", 0) > 0 and inventory.get("WHEAT", 0) == 0 and feed_left() > 0:
                # Feed rounds: the workers that reach the shed first take three or four feeds each, until every
                # hungry animal is covered. The rest take none and go straight out to the crops.
                quantity = min(stock["WHEAT"], 4, feed_left())
                action = ["PICKUP", "WHEAT", quantity]
                stock["WHEAT"] -= quantity
                feed_out[0] += quantity
            elif False and stock.get("FERTILIZER", 0) > 0 and inventory.get("FERTILIZER", 0) < min(12, eligible):
                quantity = min(stock["FERTILIZER"], min(12, eligible) - inventory.get("FERTILIZER", 0))
                action = ["PICKUP", "FERTILIZER", quantity]
                stock["FERTILIZER"] -= quantity
        if (action is None and inventory.get("MELON", 0) > 0 and position not in centers and hour < 21
                and not any(ripe_melon(c) and c not in acted and claims.get(c, unit) == unit and jobs(c) for c in desired)):
            action = _worker_move(position, min(centers, key=lambda c: (dist(position, c), c)), size)
        # 3. The last day: bring everything in before the game ends.
        if action is None and day == 29 and (products or inventory.get("WHEAT", 0) or inventory.get("FERTILIZER", 0)):
            shed = min(centers, key=lambda c: (dist(position, c), c))
            if remaining <= dist(position, shed) + 2:
                if position == shed:
                    action = ["DROP"]
                    for item, n in inventory.items():
                        stock[item] = stock.get(item, 0) + n
                else:
                    action = _worker_move(position, shed, size)
        if action is None and sum(products.values()) + surplus_wheat >= 6 and 0 < to_shed(position) <= 2 and remaining > 3:
            action = _worker_move(position, min(centers, key=lambda c: (dist(position, c), c)), size)
        # 4. Next cell: the nearest one that can be worked, own block first; what dies tonight or rots
        #    within hours comes first inside each group.
        if action is None:
            best = None
            current = state["_targets"].get(unit)
            px, py = position % size, position // size
            others = [positions[v] for v in range(number) if v != unit]
            mine_to_shed = to_shed(position)
            holds_feed, holds_fert = inventory.get("WHEAT", 0) > 0, inventory.get("FERTILIZER", 0) > 0
            last = last_worked.get(unit)
            pa = (px - (size - 1) / 2, py - (size - 1) / 2)
            pn = math.hypot(*pa)
            for cell in desired:
                if cell in acted or claims.get(cell, unit) != unit:
                    continue
                facts = cell_needs[cell]
                plan = jobs(cell)
                optional = False
                if not plan and 9 in facts and desired.get(cell) != "EMPTY":
                    plan, optional = [["WATER"]], True   # a plant with nothing due is watered only when no due cell can be reached
                if not plan:
                    continue
                if plan[0][0] == "NEED":
                    shed = shed_for(cell)
                    trip = dist(position, shed) + dist(shed, cell) + 1
                else:
                    trip = dist(position, cell)
                if trip + 1 > remaining:
                    continue
                tile = tiles[cell]
                spent = (isinstance(tile, dict) and tile.get("kind") == "PLANT" and _WORKER_CROPS[tile["crop"]][3]
                         and day - tile["planted_day"] >= _WORKER_CROPS[tile["crop"]][1] and tile.get("yield_units", 0) > 0)
                urgent = hour >= 20 and (dying(cell) or spent) or _expiring(tiles[cell], day * 24 + hour - 16)
                # A ripe melon is picked first and carried straight in: the first melons of the day sell near
                # the full price, and every one sold before ours takes about a dollar off each of ours.
                urgent = urgent or ripe_melon(cell) and ["HARVEST"] in plan
                urgent = urgent or cell in must_now and cell in mine_due[unit]
                W, cx, cy, away_shed = _CHOICE_W, cell % size, cell // size, to_shed(cell)
                near_others = [dist(o, cell) for o in others] or [99]
                is_plant = isinstance(tile, dict) and tile.get("kind") == "PLANT"
                is_animal = isinstance(tile, dict) and bool(tile.get("animal"))
                score = W[0] * trip + W[1] * (trip == 0) + W[2] * (trip == 1) + sum(W[j] for j in facts)
                score += W[12] * away_shed + W[13] * (min(near_others) < trip) + W[14] * sum(o <= 2 for o in near_others)
                score += W[15] * (3 in facts and holds_feed) + W[16] * (is_plant and holds_fert)
                score += W[19] * ((cx >= size // 2) == (px >= size // 2) and (cy >= size // 2) == (py >= size // 2))
                score += W[20] * trip * (hour >= 18) + W[26] * trip * (hour < 6)
                score += W[25] * (last is not None and dist(last, cell) == 1)
                score += W[28] * (away_shed > mine_to_shed) + W[29] * (away_shed < mine_to_shed)
                score += W[30] * (away_shed > mine_to_shed and hour < 12) + W[31] * (away_shed < mine_to_shed and hour >= 18)
                score += W[32] * sum(n in needy for n in (cell + 1, cell - 1, cell + size, cell - size)
                                     if 0 <= n < size * size and abs(n % size - cx) + abs(n // size - cy) == 1)
                score += W[33] * (min(near_others) == 0)
                ca = (cx - (size - 1) / 2, cy - (size - 1) / 2)
                score += W[34] * ((pa[0] * ca[0] + pa[1] * ca[1]) / (pn * math.hypot(*ca)) if pn > 0.8 else 0.0)
                score += W[35] * (unit == 0 and is_animal) + W[36] * (last is None) * away_shed
                # fertilizer in hand is worth a walk to a strawberry or tomato about to fruit: it doubles the next pickings
                score += _FERT_PULL * (is_plant and bool(_WORKER_CROPS[tile["crop"]][3]) and ["FERTILIZE"] in plan)
                key = (not urgent, optional, -score, cell)
                if best is None or key < best[0]:
                    best = (key, cell, plan)
            if best is None or best[1] != current:
                if claims.get(current) == unit:
                    del claims[current]
                state["_targets"].pop(unit, None)
            if best is not None:
                _, target, plan = best
                claims[target] = unit
                state["_targets"][unit] = target
                if plan[0][0] == "NEED":
                    item = plan[0][1]
                    shed = shed_for(target)
                    if position != shed:
                        action = _worker_move(position, shed, size)
                    else:
                        quantity = 1
                        if item == "WHEAT":
                            fed = {"WHEAT": 1}
                            hungry = sum(1 for c in desired if isinstance(tiles[c], dict) and tiles[c].get("animal") and not tiles[c].get("fed_today")
                                         and claims.get(c, unit) == unit and (c in home or c == target)
                                         and ["FEED"] in _route_jobs(tiles[c], desired[c], day, hour, fed, stock, seeds))
                            quantity = max(1, min(stock.get("WHEAT", 0), hungry, 8))
                        action = ["PICKUP", item, quantity]
                        stock[item] -= quantity
                elif position != target:
                    action = _worker_move(position, target, size)
                else:
                    action = plan[0]
                    acted.add(position)
        # Nothing due within reach: water the nearest plant that has not been watered today. It costs nothing
        # now and that plant is not a forced visit tomorrow.
        if action is None:
            spare = [c for c in desired if c not in acted and isinstance(tiles[c], dict) and tiles[c].get("kind") == "PLANT"
                     and not tiles[c].get("watered_today") and desired.get(c) != "EMPTY" and claims.get(c, unit) == unit
                     and not (_WORKER_CROPS[tiles[c]["crop"]][3] and day - tiles[c]["planted_day"] >= _WORKER_CROPS[tiles[c]["crop"]][1])
                     and dist(position, c) <= 3 and dist(position, c) + 1 <= remaining]
            if spare and day < 29:
                cell = min(spare, key=lambda c: (dist(position, c), c))
                if cell == position:
                    action = ["WATER"]
                    acted.add(cell)
                else:
                    action = _worker_move(position, cell, size)
                    claims[cell] = unit
        if action is None and hour >= 18 and any(n > 0 for item, n in inventory.items() if item not in ANIMAL_COST):
            shed = min(centers, key=lambda c: (dist(position, c), c))
            if position != shed:
                action = _worker_move(position, shed, size) if dist(position, shed) < remaining else None
            elif sum(inventory.values()) <= max(0, 100 - sum(stock.values())):
                action = ["DROP"]
                for item, n in inventory.items():
                    stock[item] = stock.get(item, 0) + n
        if action is None:
            action = ["PASS"]
        if action[0] == "PLANT":
            seeds[action[1]] -= 1
        if action[0] not in ("NORTH", "SOUTH", "EAST", "WEST", "PASS", "PICKUP", "DROP") and not (action[0] == "PLACE" and len(action) >= 3):
            last_worked[unit] = position
        actions.append(action)
    state["_claims"] = claims
    state["_worker_areas"] = [[] for _ in range(number)]
    return actions


def worker_actions(obs, state, desired):
    if state.get("component", 7) >= 6 and obs["day"] >= 6 and len(obs["farms"][obs["player"]]["unlocked_quadrants"]) >= 2:
        return _block_worker_actions(obs, state, desired)
    farm, private = obs["farms"][obs["player"]], obs["private"]
    size, day, hour = len(farm["tiles"]), obs["day"], obs["hour"]
    positions = [p[1] * size + p[0] for p in [farm["farmer"], *farm.get("hands", [])]]
    inventories = [dict(inv) for inv in private["inventories"]]
    tiles = [tile for row in farm["tiles"] for tile in row]
    stock, seeds = dict(private["shed"]), dict(private["seeds"])
    seeds["_CASH"] = farm.get("money", 0)
    number = len(positions)
    keep = _harvest_feed_keep(tiles, desired, day, hour, sum(inv.get("WHEAT", 0) for inv in inventories))
    if keep is not None:
        stock["WHEAT"] = min(stock.get("WHEAT", 0), keep)
        seeds["_FEED"] = int(sum(isinstance(t, dict) and bool(t.get("animal")) and not t.get("fed_today") for t in tiles)
                             > sum(inv.get("WHEAT", 0) for inv in inventories))
    cash_mode = day <= 5 or len(farm.get("unlocked_quadrants", ["NW"])) < 2
    layout_done = all(desired.get(cell, "EMPTY") == "EMPTY" or isinstance(tile, dict) and
                      (tile.get("crop") == desired[cell] or bool(tile.get("animal")) and ":" in desired[cell])
                      for cell, tile in enumerate(tiles) if tile != "LOCKED")
    def sheep_waiting():
        if day >= 28:
            return 0
        placed = sum(isinstance(t, dict) and t.get("animal") == "SHEEP" and not t.get("fed_today") for t in tiles)
        held = sum(inv.get("SHEEP", 0) for inv in inventories) + stock.get("SHEEP", 0)
        return max(0, placed + held - sum(inv.get("WHEAT", 0) for inv in inventories))
    basic, territories = state.get("component", 7) < 5, state.get("component", 7) >= 6 and day >= 6
    remaining = (23 if day == 29 else 24) - hour
    centers = [(size // 2 - 1 + dx) + (size // 2 - 1 + dy) * size for dx in (0, 1) for dy in (0, 1)]
    targets = state.get("_worker_targets", [])[:number]
    targets += [None] * (number - len(targets))
    owned = [cell for cell, tile in enumerate(tiles) if tile != "LOCKED"]
    state["fertilizer_need"] = 0 if basic else sum(_worker_fert_eligible(tiles[cell], day) and
        (tiles[cell].get("watered_today") or _worker_water_due(tiles[cell], day, fertilizing=True)) and
        min(_worker_distance(position, cell, size) for position in positions) + 1 +
        (not tiles[cell].get("watered_today")) +
        bool(tiles[cell].get("yield_units", 0) and _WORKER_CROPS[tiles[cell]["crop"]][3]) <= remaining
        for cell in owned)
    if state.get("_worker_day") != day:
        targets = [None] * number
    if territories and (state.get("_worker_day") != day or state.get("_worker_count") != number or
                        set(state.get("_worker_owners", {})) != set(owned)):
        state["_worker_owners"] = _worker_assign(owned, desired, tiles, positions,
            state.get("blocks", []), day, size, basic, targets)
    owners = state.get("_worker_owners", {}) if territories else dict.fromkeys(owned, -1)
    state["_worker_day"], state["_worker_count"] = day, number
    prices = obs.get("market", {}).get("prices", {})
    actions = []
    claimed = {cell: unit for unit, cell in enumerate(targets) if cell is not None}
    staged = set()
    for unit, position in enumerate(positions):
        inventory = inventories[unit]
        feed_needed = any(isinstance(tiles[cell], dict) and "animal" in tiles[cell] and
            not tiles[cell].get("fed_today") and desired.get(cell, "EMPTY") not in {"EMPTY", *_WORKER_CROPS} and
            not (tiles[cell]["animal"] == "SHEEP" and day >= 28) for cell in owned)
        urgent_cash = (farm.get("money", 0) < 25 and inventory.get("FERTILIZER", 0) > 0
                       and stock.get("WHEAT", 0) == 0 and feed_needed)
        service_inventory = dict(inventory)
        if urgent_cash or cash_mode:
            service_inventory["FERTILIZER"] = 0
        def plan(cell):
            if (day == 0 and unit > 0 and isinstance(tiles[cell], dict) and tiles[cell].get("animal")
                    and any(seeds.get(crop, 0) > 0 for crop in _WORKER_CROPS)):
                return []   # hands plant while there are seeds; the farmer tends the animals
            jobs = _worker_plan(tiles[cell], desired.get(cell, "EMPTY"), day, hour,
                               service_inventory, stock, seeds, basic)
            # Scarce feed goes to the sheep first: no feed trip for another animal while a sheep waits.
            if (jobs and jobs[0] == ["NEED", "WHEAT"] and tiles[cell].get("animal") != "SHEEP"
                    and stock.get("WHEAT", 0) <= sheep_waiting()):
                reduced = dict(stock)
                reduced["WHEAT"] = 0
                jobs = _worker_plan(tiles[cell], desired.get(cell, "EMPTY"), day, hour,
                                    service_inventory, reduced, seeds, basic)
            beast = tiles[cell]
            if (day == 2 and isinstance(beast, dict) and beast.get("crop") == "MELON" and beast["planted_day"] < day
                    and not beast.get("watered_today") and ["WATER"] not in jobs and layout_done):
                jobs = jobs + [["WATER"]]   # spare time on day 2 puts every melon on the same watering days (2 and 4)
            if (1 <= day <= 5 and isinstance(beast, dict) and beast.get("animal") and not beast.get("cared_today")
                    and ["CARE"] not in jobs and desired.get(cell, "EMPTY") not in {"EMPTY", *_WORKER_CROPS}
                    and (beast.get("fed_today") or _animal_service(beast, day, True)[0])
                    and (keep is None or beast.get("fed_today") or inventory.get("WHEAT", 0) > 0)
                    and not (jobs and jobs[0][0] == "NEED")):
                jobs = [["CARE"]] + jobs
            label = desired.get(cell, "EMPTY")
            if (jobs and ["HARVEST"] in jobs and ":" in label and isinstance(tiles[cell], dict) and tiles[cell].get("kind") == "PLANT"
                    and not inventory.get(label.split(":")[1], 0) and stock.get(label.split(":")[1], 0) > 0
                    and min(_worker_distance(position, shed, size) for shed in centers) <= _worker_distance(position, cell, size)):
                jobs = [["NEED", label.split(":")[1]]]
            if jobs and jobs[0][0] == "NEED":
                trip = min(_worker_distance(position, shed, size) +
                    _worker_distance(shed, cell, size) + 2 for shed in centers)
                if trip > remaining:
                    reduced = dict(stock)
                    reduced[jobs[0][1]] = 0
                    jobs = _worker_plan(tiles[cell], desired.get(cell, "EMPTY"), day, hour,
                                        service_inventory, reduced, seeds, basic)
            return jobs
        target = targets[unit]
        if target is not None and (target not in owned or claimed.get(target) != unit or not plan(target)):
            if claimed.get(target) == unit:
                del claimed[target]
            target = None
        shed_distance = min(_worker_distance(position, shed, size) for shed in centers)
        terminal_stock = sum(n for item, n in inventory.items() if item not in {"GOOSE", "COW", "SHEEP"})
        terminal_delivery = day == 29 and terminal_stock > 0 and remaining <= shed_distance + 2
        if terminal_delivery and target is not None:
            claimed.pop(target, None)
            target = None
        def dying(cell):
            tile = tiles[cell]
            return (isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today")
                    and tile.get("consecutive_unwatered", 0) >= 1 and desired.get(cell, "EMPTY") != "EMPTY"
                    and not (_WORKER_CROPS[tile["crop"]][3] and day - tile["planted_day"] >= _WORKER_CROPS[tile["crop"]][1]))
        def starving(cell):
            tile = tiles[cell]
            return (isinstance(tile, dict) and tile.get("animal") and not tile.get("fed_today")
                    and (tile.get("consecutive_unfed", 0) >= 1 or day <= 5 and hour >= 12 and tile["animal"] == "SHEEP")
                    and not (tile["animal"] == "SHEEP" and day >= 28)
                    and desired.get(cell, "EMPTY") not in {"EMPTY", *_WORKER_CROPS})
        rescue = None
        # A worker holding feed while an animal is about to go hungry feeds it; the others save the dry plants.
        def mine_to_feed(cell):
            # an unfed animal is open to a worker holding feed even if a worker without feed is walking to it
            holder = claimed.get(cell)
            return holder in (None, unit) or (day <= 5 and inventory.get("WHEAT", 0) > 0
                                             and inventories[holder].get("WHEAT", 0) == 0)
        feeding_first = day <= 5 and inventory.get("WHEAT", 0) > 0 and any(
            starving(cell) and mine_to_feed(cell) for cell in owned)
        # A worker carrying an animal to its cell is not called away.
        placing_now = (day <= 5 and target is not None and bool(plan(target)) and (
            any(inventory.get(a, 0) > 0 for a in ("GOOSE", "COW", "SHEEP"))
            or plan(target)[0][0] == "NEED" and plan(target)[0][1] in ("GOOSE", "COW", "SHEEP")))
        covered = day <= 5 and inventory.get("WHEAT", 0) == 0 and (
            sum(inv.get("WHEAT", 0) for inv in inventories) >= sum(bool(starving(cell)) for cell in owned))
        # Standing at the shed with fertilizer in hand: put it down first, then go.
        unload_first = (day <= 5 and hour >= 14 and position in centers and inventory.get("FERTILIZER", 0) > 0
                        and inventory.get("WHEAT", 0) == 0 and (target is None or dying(target)))
        if unload_first and target is not None:
            claimed.pop(target, None)
            target = None
        if hour >= 14 and not feeding_first and not placing_now and not unload_first and not (target is not None and dying(target)):
            open_dying = [cell for cell in owned if dying(cell) and claimed.get(cell) in (None, unit)
                          and _worker_distance(position, cell, size) + 1 <= remaining and plan(cell)]
            if open_dying:
                rescue = min(open_dying, key=lambda cell: (_worker_distance(position, cell, size), cell))
                if target is not None:
                    claimed.pop(target, None)
                target = rescue
                claimed[rescue] = unit
        # Before the second land, a worker carrying wool, milk or eggs delivers them first: that cash buys the land.
        carrying_cash = (cash_mode and day > 5 and hour < 14
                         and any(inventory.get(item, 0) > 0 for item in ("WOOL", "MILK", "EGG")))
        if (rescue is None and not carrying_cash and not placing_now and not covered
                and not (target is not None and starving(target))
                and (inventory.get("WHEAT", 0) > 0 or hour >= 4 and stock.get("WHEAT", 0) > 0)):
            open_starving = [cell for cell in owned if starving(cell) and mine_to_feed(cell)
                             and plan(cell)]
            if open_starving:
                rescue = min(open_starving, key=lambda cell: (_worker_distance(position, cell, size), cell))
                if target is not None:
                    claimed.pop(target, None)
                target = rescue
                if claimed.get(rescue) not in (None, unit):
                    targets[claimed[rescue]] = None
                claimed[rescue] = unit
        force_delivery = False
        if (rescue is None and cash_mode and (inventory.get("FERTILIZER", 0) >= 1 or day > 5 and any(inventory.get(item, 0) > 0 for item in ("WOOL", "MILK", "EGG")))
                and (farm.get("money", 0) < 400 or day > 5) and not terminal_delivery
                and not (day <= 5 and hour >= 14 and target is not None and dying(target))
                and (day > 5 and any(inventory.get(item, 0) > 0 for item in ("WOOL", "MILK", "EGG"))
                     or not (isinstance(tiles[position], dict) and tiles[position].get("animal") and plan(position)))):
            if target is not None:
                claimed.pop(target, None)
            target, force_delivery = None, True
        # Preserve a visit before chaining its newly collected fertilizer.
        wool_waiting = (cash_mode and day > 5 and not (isinstance(tiles[position], dict) and tiles[position].get("yield_units", 0) > 0)
                        and any(isinstance(tiles[cell], dict) and tiles[cell].get("animal") and tiles[cell].get("yield_units", 0) > 0
                                and cell not in claimed for cell in owned))
        if rescue is None and target is None and position in owned and position not in claimed and plan(position) and (
                not territories or owners.get(position) == unit) and not terminal_delivery and not force_delivery and not wool_waiting:
            target = position
        if target is None and not basic and inventory.get("FERTILIZER", 0) > 0 and not terminal_delivery and not urgent_cash:
            eligible = [cell for cell in owned if cell not in claimed and _worker_fert_eligible(tiles[cell], day)
                and _worker_distance(position, cell, size) + 1 + (not tiles[cell].get("watered_today"))
                + bool(tiles[cell].get("yield_units", 0) and _WORKER_CROPS[tiles[cell]["crop"]][3]) <= remaining]
            if eligible:
                target = min(eligible, key=lambda cell: (_worker_distance(position, cell, size), cell))
        feed_reserve = sum(isinstance(tiles[cell], dict) and "animal" in tiles[cell] and
            not tiles[cell].get("fed_today") for cell in owned if not territories or owners.get(cell) == unit)
        sellable = sum(n for item, n in inventory.items() if item not in {"WHEAT", "FERTILIZER", "GOOSE", "COW", "SHEEP"})
        sellable += max(0, inventory.get("WHEAT", 0) - feed_reserve)
        delivery = (sellable >= 8 or urgent_cash or force_delivery or (day == 29 and terminal_stock > 0)
                    or (day <= 5 and inventory.get("FERTILIZER", 0) >= 2)
                    or (day <= 5 and inventory.get("FERTILIZER", 0) >= 1 and farm.get("money", 0) < 400))
        if target is None and delivery:
            shed = min(centers, key=lambda cell: (_worker_distance(position, cell, size), cell))
            if position == shed:
                room = max(0, 100 - sum(stock.values()))
                if (day <= 5 and feed_needed and inventory.get("WHEAT", 0) > 0
                        and 0 < inventory.get("FERTILIZER", 0) <= room):
                    # feed in hand stays in hand: only the fertilizer goes into the shed
                    action = ["PLACE", "FERTILIZER", inventory["FERTILIZER"]]
                    stock["FERTILIZER"] = stock.get("FERTILIZER", 0) + inventory["FERTILIZER"]
                elif room >= sum(inventory.values()):
                    action = ["DROP"]
                    for item, quantity in inventory.items():
                        stock[item] = stock.get(item, 0) + quantity
                else:
                    products = [item for item, quantity in inventory.items() if quantity > 0
                                and item not in {"GOOSE", "COW", "SHEEP"}]
                    if room > 0 and products:
                        item = max(products, key=lambda item: (prices.get(item, 1) * min(room, inventory[item]), item))
                        quantity = min(room, inventory[item])
                        action = ["PLACE", item, quantity]
                        stock[item] = stock.get(item, 0) + quantity
                    else:
                        action = ["PASS"]  # Market sales can free space after this action.
            else:
                action = _worker_move(position, shed, size)
            actions.append(action)
            targets[unit] = None
            continue
        if target is None:
            def open_to_me(cell):
                # A free worker may take over a job another worker is still walking to, if it is clearly closer.
                holder = claimed.get(cell)
                if holder is not None and holder != unit and isinstance(tiles[cell], dict) and tiles[cell].get("animal")                         and not tiles[cell].get("fed_today") and mine_to_feed(cell):
                    return True
                if day <= 5 and ":" in desired.get(cell, "") and not (isinstance(tiles[cell], dict) and tiles[cell].get("animal")):
                    return holder is None     # a cell waiting for its animal stays with the worker fetching it
                return holder is None or (holder != unit and positions[holder] != cell and
                    _worker_distance(position, cell, size) + 2 <= _worker_distance(positions[holder], cell, size))
            candidates = [cell for cell in owned if open_to_me(cell) and plan(cell)
                and _worker_distance(position, cell, size) + (2 if plan(cell)[0][0] == "PLANT" else 1) <= remaining]
            local = [cell for cell in candidates if not territories or owners.get(cell) == unit]
            def placing(cell):
                first = plan(cell)[0]
                return (first[0].startswith("BUILD_") or first[0] == "PLACE"
                        or first[0] == "NEED" and first[1] in ("GOOSE", "COW", "SHEEP"))
            place = [cell for cell in candidates if placing(cell)]
            def feeds(cell):
                return (inventory.get("WHEAT", 0) > 0 and isinstance(tiles[cell], dict) and tiles[cell].get("animal")
                        and not tiles[cell].get("fed_today") and ["FEED"] in plan(cell))
            def feed_wheat(cell):
                return (isinstance(tiles[cell], dict) and tiles[cell].get("crop") == "WHEAT"
                        and tiles[cell].get("yield_units", 0) > 0 and desired.get(cell) != "WHEAT")
            feed_gap = 0
            if keep is not None and inventory.get("WHEAT", 0) == 0:
                # wheat still to be harvested this morning so that every animal is fed from it
                feed_gap = (sum(isinstance(t, dict) and bool(t.get("animal")) and not t.get("fed_today") for t in tiles)
                            - sum(inv.get("WHEAT", 0) for inv in inventories)
                            - sum(tiles[cell]["yield_units"] + 1 for cell, holder in claimed.items() if holder != unit and feed_wheat(cell)))
            urgent = [cell for cell in candidates if _worker_rank(tiles[cell], day, hour, prices)[0] == 0
                      and (owners.get(cell) == unit or not territories or hour >= 12
                           or _worker_distance(position, cell, size) <= 4)]
            if place:
                held = [cell for cell in place if plan(cell)[0][0] != "NEED"]
                target = min(held or place, key=lambda cell: (_worker_distance(position, cell, size), cell))
            elif cash_mode and any(isinstance(tiles[cell], dict) and tiles[cell].get("animal")
                                  and (tiles[cell].get("fertilizer_available") or tiles[cell].get("yield_units", 0) > 0) for cell in candidates):
                # Opener cash comes from fertilizer: animals holding it are visited before anything else.
                target = min((cell for cell in candidates if isinstance(tiles[cell], dict) and tiles[cell].get("animal")
                              and (tiles[cell].get("fertilizer_available") or tiles[cell].get("yield_units", 0) > 0)),
                             key=lambda cell: (day > 5 and tiles[cell].get("yield_units", 0) <= 0,
                                               _worker_distance(position, cell, size), cell))
            elif day <= 5 and any(feeds(cell) for cell in candidates):
                # wheat in hand goes to the nearest unfed animal before any other job
                target = min((cell for cell in candidates if feeds(cell)),
                             key=lambda cell: (_worker_distance(position, cell, size), cell))
            elif feed_gap > 0 and any(feed_wheat(cell) for cell in candidates):
                target = min((cell for cell in candidates if feed_wheat(cell)),
                             key=lambda cell: (_worker_distance(position, cell, size), cell))
            elif urgent:
                target = min(urgent, key=lambda cell: (_worker_distance(position, cell, size), cell))
            elif local:
                def order(cell):
                    if tiles[cell] is None and day <= 5:
                        return (4, -_ITEM_COST.get(desired.get(cell), 0))
                    return _worker_rank(tiles[cell], day, hour, prices)
                def stranded(cell):
                    # Opener: at similar distance take the cell with fewer open neighbours, so no
                    # single cell is left behind for a long walk back.
                    if day > 5 or tiles[cell] is not None:
                        return 0
                    x, y = cell % size, cell // size
                    return sum(0 <= x + dx < size and 0 <= y + dy < size
                               and (x + dx) + (y + dy) * size in local and tiles[(x + dx) + (y + dy) * size] is None
                               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                def others_closer(cell):
                    # Opener: a worker first takes the open cells it is nearest to of all workers,
                    # which splits the field by where each worker's animal left it.
                    if day > 5 or tiles[cell] is not None:
                        return 0
                    mine = _worker_distance(position, cell, size)
                    return int(any(_worker_distance(other, cell, size) < mine or
                                   (_worker_distance(other, cell, size) == mine and index < unit)
                                   for index, other in enumerate(positions) if index != unit))
                if day <= 5:
                    # Opener cash comes from fertilizer: animals holding it are visited first each morning.
                    target = min(local, key=lambda cell: (-1 if isinstance(tiles[cell], dict) and tiles[cell].get("animal")
                            and tiles[cell].get("fertilizer_available") else 1 if feeds(cell) else
                            _worker_rank(tiles[cell], day, hour, prices)[0] if tiles[cell] is not None else 4,
                        others_closer(cell), 2 * _worker_distance(position, cell, size) + stranded(cell), cell))
                else:
                    target = min(local, key=lambda cell: (*order(cell),
                        2 * _worker_distance(position, cell, size) + stranded(cell), cell))
            elif candidates:
                # Spare workers transfer ownership before helping a nearby area.
                target = min(candidates, key=lambda cell: (_worker_distance(position, cell, size),
                    *_worker_rank(tiles[cell], day, hour, prices), cell))
        if target is None:
            # Nothing to do right now: wait where the next job will appear, not where the last one ended.
            # A cell waiting for an animal is served from the shed; a cell waiting for a seed is served on the spot.
            waiting = [cell for cell in owned if cell not in staged and desired.get(cell, "EMPTY") != "EMPTY" and (
                tiles[cell] is None or (isinstance(tiles[cell], dict) and tiles[cell].get("kind") == "PLANT"
                                        and tiles[cell]["crop"] in ("WHEAT", "CARROT")
                                        and desired.get(cell) != tiles[cell]["crop"]))]
            spot = None
            if any(":" in desired[cell] for cell in waiting) and "shed" not in staged:
                spot = min(centers, key=lambda cell: (_worker_distance(position, cell, size), cell))
                staged.add("shed")
            elif waiting:
                spot = min(waiting, key=lambda cell: (_worker_distance(position, cell, size), cell))
                staged.add(spot)
            actions.append(_worker_move(position, spot, size) if spot is not None and spot != position else ["PASS"])
            targets[unit] = None
            continue
        previous = claimed.get(target)
        if previous is not None and previous != unit:
            targets[previous] = None
        claimed[target], targets[unit] = unit, target
        if territories:
            owners[target] = unit
        jobs = plan(target)
        if not jobs:   # the job vanished between choosing and acting: never crash, just release it
            claimed.pop(target, None)
            targets[unit] = None
            actions.append(["PASS"])
            continue
        if jobs[0][0] == "NEED":
            item = jobs[0][1]
            shed = min(centers, key=lambda cell: (_worker_distance(position, cell, size), cell))
            if position == shed:
                need = sum(isinstance(tiles[cell], dict) and "animal" in tiles[cell] and
                    not tiles[cell].get("fed_today") and not (tiles[cell]["animal"] == "SHEEP" and day >= 28)
                    for cell in owned if not territories or owners.get(cell) == unit) if item == "WHEAT" else 1
                quantity = min(stock.get(item, 0), max(1, need), max(1, (stock.get(item, 0) + number - unit - 1) // (number - unit)))
                if day == 0 and unit == 0 and item == "WHEAT":
                    quantity = min(stock.get(item, 0), max(1, need))
                elif item == "WHEAT":
                    quantity = min(quantity, 3)
                action = ["PICKUP", item, quantity]
                stock[item] -= quantity
                # Fetching an animal: take its first feed on the same shed visit (build, place, feed, care in one trip).
                # When feed is scarce the sheep get it before the cows.
                if (day >= 1 and item != "WHEAT" and inventory.get("WHEAT", 0) == 0 and stock.get("WHEAT", 0) > 0
                        and (item == "SHEEP" or stock.get("WHEAT", 0) > sheep_waiting())):
                    stock[item] += quantity
                    action = ["PICKUP", "WHEAT", 1]
                    stock["WHEAT"] -= 1
            else:
                action = _worker_move(position, shed, size)
        elif position != target:
            action = _worker_move(position, target, size)
        else:
            action = jobs[0]
            if action[0] == "PLANT":
                seeds[action[1]] -= 1
        actions.append(action)
    state["_worker_targets"], state["_worker_owners"] = targets, owners
    state["_worker_areas"] = [[cell for cell in owned if owners.get(cell) == unit] for unit in range(number)]
    return actions

import copy

import math

from collections import Counter

MARKET_PARAMS = {
    "WHEAT": (25, 10000, 400, "sqrt", .80, "log", .20),
    "CARROT": (35, 10000, 450, "hinge", 1., "sqrt", .70),
    "TOMATO": (60, 10000, 200, "hinge", .40, "sqrt", .60),
    "STRAWBERRY": (120, 10000, 100, "sqrt", .70, "linear", 1.60),
    "MELON": (250, 10000, 300, "log", .20, "sq", 3.60),
    "EGG": (50, 10000, 332, "hinge", .40, "log", .20),
    "MILK": (160, 10000, 122, "sqrt", .60, "linear", 1.60),
    "WOOL": (200, 10000, 105, "log", .20, "sq", 3.20),
    "FERTILIZER": (100, 10000, 200, "linear", .40, "linear", .40),
}

CROP_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}

ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}

PRODUCT_BY_ANIMAL = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}

CROP_FIRST = {"WHEAT": 2, "CARROT": 2, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10}

CROP_LAST = {"WHEAT": 4, "CARROT": 3, "TOMATO": 11, "STRAWBERRY": 16, "MELON": 12}

SHOP_DEMAND = {
    "BAKERY": {"EGG": 1, "WHEAT": 1},
    "PIZZA_SHOP": {"MILK": 1, "TOMATO": 1, "WHEAT": 1},
    "BRUNCH_SPOT": {"EGG": 1, "WHEAT": 1, "STRAWBERRY": 1},
    "YARN_STORE": {"WOOL": 2},
    "ICE_CREAM_SHOP": {"STRAWBERRY": 1, "MILK": 1, "WHEAT": 1},
    "PET_CAFE": {"CARROT": 2},
    "SMOOTHIE_SHOP": {"STRAWBERRY": 1, "MILK": 1},
    "FARMERS_MARKET": {"WHEAT": 1, "CARROT": 1, "TOMATO": 1, "STRAWBERRY": 1},
}

RIVAL_BUDGET_MARGIN = 100

def _shape(name, value, throughput):
    value = max(0., value)
    if name == "sq":
        return value * value
    if name == "sqrt":
        return math.sqrt(value)
    if name == "log":
        return math.log1p(value)
    if name == "log10":
        return math.log10(1 + value)
    if name == "hinge":
        unit = value / throughput
        return unit + 8 * max(0., unit - 1.) ** 2
    return value

def forecast_price(obs, item, inventory):
    base, anchor, throughput, below_shape, below_target, above_shape, above_target = MARKET_PARAMS[item]
    params = obs.get("market", {}).get("params", {}).get(item, {})
    base, anchor, throughput = params.get("base", base), params.get("I0", anchor), params.get("T", throughput)
    below = inventory < anchor
    name = params.get("below_func" if below else "above_func", below_shape if below else above_shape)
    target = params.get("below_target" if below else "above_target", below_target if below else above_target)
    change = target * base * _shape(name, abs(inventory - anchor), throughput) / _shape(name, throughput, throughput)
    return max(1, round(base + change if below else base - change))

def projected_shed(obs, unit_actions):
    """Apply the input-changing field actions in worker order on private copies."""
    farm = obs["farms"][obs["player"]]
    tiles, private = copy.deepcopy((farm["tiles"], obs["private"]))
    shed = private.setdefault("shed", {})
    seeds = private.setdefault("seeds", {})
    inventories = private.setdefault("inventories", [])
    positions = [farm["farmer"]] + list(farm.get("hands", []))
    demand = Counter(a[1] for a in unit_actions if isinstance(a, list) and len(a) > 1 and a[0] == "PLANT")
    blocked = {crop for crop, amount in demand.items() if amount > seeds.get(crop, 0)}
    size = len(tiles)
    access = {(size // 2 - 1 + x, size // 2 - 1 + y) for x in (0, 1) for y in (0, 1)}
    for index, ((x, y), action) in enumerate(zip(positions, unit_actions)):
        if not isinstance(action, list) or not action:
            continue
        while len(inventories) <= index:
            inventories.append({})
        inv = inventories[index]
        tile = tiles[y][x]
        op = action[0]
        if op == "DROP" and (x, y) in access:
            for item, amount in list(inv.items()):
                accepted = min(max(0, amount), max(0, 100 - sum(shed.values())))
                shed[item] = shed.get(item, 0) + accepted
            inv.clear()  # Overflow is discarded by DROP.
        elif op == "PICKUP" and (x, y) in access and len(action) > 1:
            item = action[1]
            amount = max(0, min(action[2] if len(action) > 2 else 1, shed.get(item, 0)))
            shed[item] = shed.get(item, 0) - amount
            inv[item] = inv.get(item, 0) + amount
        elif op == "PLACE" and len(action) > 1:
            item = action[1]
            structure = "COOP" if item == "GOOSE" else "PASTURE"
            if item in ANIMAL_COST and isinstance(tile, dict) and tile.get("kind") == structure and not tile.get("animal"):
                if inv.get(item, 0) > 0:
                    inv[item] -= 1
                    tile["animal"] = item
            elif (x, y) in access:
                amount = max(0, min(action[2] if len(action) > 2 else 1, inv.get(item, 0), 100 - sum(shed.values())))
                inv[item] = inv.get(item, 0) - amount
                shed[item] = shed.get(item, 0) + amount
        elif op == "PLANT" and len(action) > 1 and tile is None:
            crop = action[1]
            if crop in CROP_COST and crop not in blocked and seeds.get(crop, 0) > 0:
                seeds[crop] -= 1
                tiles[y][x] = {"kind": "PLANT", "crop": crop, "planted_day": obs["day"], "yield_units": 0}
        elif op == "DIG" and tile is not None and tile != "LOCKED" and not (isinstance(tile, dict) and tile.get("animal")):
            tiles[y][x] = None
        elif op in ("BUILD_COOP", "BUILD_PASTURE") and tile is None:
            tiles[y][x] = {"kind": op.removeprefix("BUILD_")}
        elif isinstance(tile, dict):
            if op == "HARVEST" and tile.get("yield_units", 0) > 0:
                product = tile.get("crop") or PRODUCT_BY_ANIMAL.get(tile.get("animal"))
                mature = "crop" not in tile or obs["day"] - tile["planted_day"] >= CROP_FIRST[tile["crop"]]
                if product and mature:
                    inv[product] = inv.get(product, 0) + tile["yield_units"]
                    tile["yield_units"] = 0
                    if product in ("WHEAT", "CARROT", "MELON"):
                        tiles[y][x] = None
            elif op == "FEED" and tile.get("animal") and not tile.get("fed_today") and inv.get("WHEAT", 0) > 0:
                inv["WHEAT"] -= 1
                tile["fed_today"] = True
            elif op == "FERTILIZE" and tile.get("kind") == "PLANT" and inv.get("FERTILIZER", 0) > 0:
                inv["FERTILIZER"] -= 1
                tile["fertilized_until_day"] = max(tile.get("fertilized_until_day", -1), obs["day"] + 2)
            elif op == "COLLECT_FERTILIZER" and tile.get("animal") and tile.get("fertilizer_available"):
                inv["FERTILIZER"] = inv.get("FERTILIZER", 0) + 1
                tile["fertilizer_available"] = False
    return shed, inventories, seeds, tiles

def midgame_sell_quantity(obs, item, amount):
    """Planner's bounded hold rule, using visible next-day output and shop drain."""
    if amount <= 0:
        return 0
    farm = obs["farms"][obs["player"]]
    current = obs["market"]["prices"].get(item, MARKET_PARAMS[item][0])
    inventory = obs["market"]["inventory"]
    if item not in inventory or farm["money"] < 500 or sum(obs["private"]["shed"].values()) >= 85:
        return amount
    drain = int(item != "FERTILIZER") + 6 * sum(SHOP_DEMAND.get(shop, {}).get(item, 0) for shop in obs.get("town", {}).get("unlocked_shops", []))
    supply = 0
    for row in farm["tiles"]:
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("crop") == item:
                age = obs["day"] - tile["planted_day"]
                if item in ("WHEAT", "CARROT", "MELON") and age + 1 >= CROP_LAST[item]:
                    supply += max(tile.get("yield_units", 0), {"WHEAT": 4, "CARROT": 3, "MELON": 6}[item])
                elif item in ("TOMATO", "STRAWBERRY") and age + 1 >= CROP_FIRST[item]:
                    supply += min(4, 1 + (1 - max(0, CROP_FIRST[item] - age)) // (1 if item == "TOMATO" else 2))
            elif PRODUCT_BY_ANIMAL.get(tile.get("animal")) == item:
                first, interval = {"GOOSE": (4, 1), "COW": (8, 2), "SHEEP": (6, 3)}[tile["animal"]]
                offset = max(0, first - (obs["day"] - tile.get("placed_day", obs["day"])))
                if offset <= 1:
                    supply += 1 + (1 - offset) // interval
    tomorrow = forecast_price(obs, item, inventory[item] - drain + supply)
    hold = min(12, amount) if tomorrow >= current * 1.15 and current < MARKET_PARAMS[item][0] else 0
    return amount - hold

def market_orders(obs, state, desired, hands_target, land_due, unit_actions):
    farm = obs["farms"][obs["player"]]
    day, step = obs["day"], obs["step"]
    component = state.get("component", 7)
    shed, inventories, seeds, tiles = projected_shed(obs, unit_actions)
    carried = Counter()
    for inventory in inventories:
        carried.update(inventory)
    live = Counter(t["animal"] for row in tiles for t in row if isinstance(t, dict) and t.get("animal"))
    areas = state.get("_worker_areas") if day >= 6 else None
    if areas:
        flat = [t for row in tiles for t in row]
        carried_feed = sum(min(inv.get("WHEAT", 0), sum(isinstance(flat[c], dict) and bool(flat[c].get("animal")) and not flat[c].get("fed_today")
                           for c in areas[u])) for u, inv in enumerate(inventories) if u < len(areas))
    else:
        carried_feed = carried["WHEAT"]
    total_animals = {animal: live[animal] + shed.get(animal, 0) + carried[animal] for animal in ANIMAL_COST}
    animal_target, seed_target = Counter(), Counter()
    filler_seeds = 0
    for cell, label in sorted(desired.items()):
        x, y = cell % 10, cell // 10
        tile = tiles[y][x]
        if tile == "LOCKED":
            continue
        if ":" in label:
            animal = label.split(":", 1)[1]
            if animal in ANIMAL_COST:
                animal_target[animal] += 1
        elif label in CROP_COST and day + CROP_FIRST[label] <= 29:
            ready = tile is None or isinstance(tile, dict) and tile.get("kind") == "WEED"
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                crop, age = tile["crop"], day - tile["planted_day"]
                ready |= (crop in ("WHEAT", "CARROT", "MELON") and tile.get("yield_units", 0) > 0 and age >= CROP_FIRST[crop])
                ready |= crop in ("TOMATO", "STRAWBERRY") and age >= CROP_LAST[crop] - 1
            if day <= 5 and isinstance(tile, dict) and tile.get("crop") == label:
                ready = False
            seed_target[label] += bool(ready)
        if tile is None and label != "WHEAT" and label != "EMPTY" and 6 <= day <= 24 and filler_seeds < 30:
            seed_target["WHEAT"] += 1
            filler_seeds += 1
    owned = len(farm.get("unlocked_quadrants", ["NW"]))
    if component >= 2 and land_due and owned < 4:
        state["pending_land_target"] = max(state.get("pending_land_target", owned), owned + 1)
    pending_land = owned < state.get("pending_land_target", owned) if component >= 2 else bool(land_due and owned < 4)
    # Desired animals are tomorrow's feeding liability before their first PLACE.
    retained_live = Counter(t['animal'] for cell,t in enumerate(tile for row in tiles for tile in row)
        if isinstance(t,dict) and t.get('animal')
        and desired.get(cell,t['kind']+':'+t['animal']) not in (*CROP_COST,'EMPTY'))
    feed_need = sum(max(retained_live[a],animal_target[a]) for a in ANIMAL_COST if a != "SHEEP" or day < 28)
    if day >= 1:
        animals_now = [t for row in tiles for t in row if isinstance(t, dict) and t.get("animal")]
        feed_need = sum(not t.get("fed_today") and _animal_service(t, day, day <= 5)[0] for t in animals_now)
    fertilizer_need = state.get("fertilizer_need")
    if fertilizer_need is None:
        fertilizer_need = sum(t.get("kind") == "PLANT" and t.get("fertilized_until_day", -1) < day
                              and day - t["planted_day"] in {"WHEAT": (2,), "CARROT": (2,), "TOMATO": (7, 10), "STRAWBERRY": (9, 13)}.get(t.get("crop"), ())
                              for row in tiles for t in row if isinstance(t, dict))
    pending = {
        "hire": {"HIRE": max(0, hands_target - len(farm.get("hands", [])))},
        "land": {"BUY_LAND": int(pending_land)},
        "animal": {a: max(0, animal_target[a] - total_animals[a]) for a in ANIMAL_COST},
        "seed": {c: max(0, seed_target[c] - seeds.get(c, 0)) for c in CROP_COST},
        "feed": {"WHEAT": max(0, feed_need - shed.get("WHEAT", 0) - carried_feed)},
    }
    if component >= 2:
        state["pending_purchases"] = pending
        state["pending_seed_deadlines"] = {crop: 29 - CROP_FIRST[crop] for crop in CROP_COST}
    starving_now = sum(isinstance(t, dict) and bool(t.get("animal")) and not t.get("fed_today")
                       and t.get("consecutive_unfed", 0) >= 1 and not (t["animal"] == "SHEEP" and day >= 28)
                       for row in tiles for t in row)
    starving_unfunded = (starving_now > shed.get("WHEAT", 0) + carried["WHEAT"]
                         and farm["money"] < 40 * (starving_now - shed.get("WHEAT", 0) - carried["WHEAT"]))
    final = step >= 700
    feed_quote = forecast_price(obs, "WHEAT", obs["market"]["inventory"]["WHEAT"] - 1)
    emergency_feed_cash = pending["feed"]["WHEAT"] > 0 and farm["money"] < feed_quote
    sales = []
    for item in MARKET_PARAMS:
        reserve = 0
        if not final and item == "WHEAT":
            reserve = max(0, feed_need - carried_feed)
            keep = _harvest_feed_keep([t for row in tiles for t in row], desired, day, obs["hour"], carried["WHEAT"])
            if keep is not None:
                reserve = keep
            if areas and day < 28:   # tomorrow's feed stays in the shed
                reserve += sum(live.values())
            if day == 0:
                wanted = (sum(pending["seed"][c] * CROP_COST[c] for c in CROP_COST)
                          + sum(pending["animal"][a] * ANIMAL_COST[a] for a in ANIMAL_COST)
                          + 2 * pending["hire"]["HIRE"])
                short = wanted - farm["money"]
                quote = max(1, obs["market"]["prices"].get("WHEAT", 25) - 2)
                reserve = int(max(0, shed.get("WHEAT", 0) - max(0, -(-short // quote)))) if short > 0 else shed.get("WHEAT", 0)
                # every sheep is fed on day 0: one missed day costs a whole wool on day 6
                reserve = max(reserve, min(shed.get("WHEAT", 0), 3 - carried["WHEAT"]))
        elif not final and item == "FERTILIZER":
            reserve = 0 if emergency_feed_cash else max(0, fertilizer_need - carried["FERTILIZER"])
        amount = max(0, shed.get(item, 0) - reserve)
        if not final and not pending_land and component >= 7 and not starving_unfunded:
            projected_obs = {**obs, "private": {**obs["private"], "shed": shed}}
            amount = midgame_sell_quantity(projected_obs, item, amount)
        if amount:
            sales.append(["SELL", item, amount])
    if obs["hour"] == 23 and not final:
        # At midnight every worker's load drops into the shed, and what does not fit is lost.
        # Make room now: sell reserves, cheapest first (they can be bought back in the morning).
        selling = {order[1]: order[2] for order in sales}
        excess = sum(shed.values()) - sum(selling.values()) + sum(carried.values()) - 100
        for item in sorted(MARKET_PARAMS, key=lambda k: (k not in ("FERTILIZER", "WHEAT"), obs["market"]["prices"].get(k, 1))):
            if excess <= 0:
                break
            more = min(excess, shed.get(item, 0) - selling.get(item, 0))
            if more > 0:
                selling[item] = selling.get(item, 0) + more
                excess -= more
        sales = [["SELL", item, amount] for item, amount in selling.items() if amount > 0]
    sales.sort(key=lambda order: (-order[2] * obs["market"]["prices"].get(order[1], 1), order[1]))
    if final:
        if component >= 2:
            state["pending_purchases"] = {}
        return sales[:10]
    input_slots = min(4, pending["hire"]["HIRE"] + int(pending_land)
                      + sum(bool(n) for category in ("animal", "seed", "feed") for n in pending[category].values()))
    input_slots = max(input_slots, min(9, pending["hire"]["HIRE"]))
    orders = sales[:max(1, 10 - input_slots)]
    budget = farm["money"]
    inventory = dict(obs["market"]["inventory"])
    for _, item, amount in orders:
        inv = inventory[item] + RIVAL_BUDGET_MARGIN
        for _ in range(amount):
            quote = forecast_price(obs, item, inv)
            if component >= 2:
                budget += quote
            inv += quote > 1
        # Actual own supply bounds the next purchase budget conservatively.
        inventory[item] += amount
        shed[item] -= amount
    room = max(0, 100 - sum(shed.values()))
    midnight_full = day >= 6 and obs["hour"] == 23 and sum(shed.values()) + sum(carried.values()) >= 100
    hires = farm.get("hires_today", len(farm.get("hands", [])))
    if day <= 5 and pending["hire"]["HIRE"] and shed.get("WHEAT", 0) > 0 and len(orders) < 10 - pending["hire"]["HIRE"]:
        # Hands come first: if the cash does not cover today's hires, feed wheat is sold to pay them.
        a, b, wages = 1, 1, 0
        for index in range(hires + pending["hire"]["HIRE"]):
            wages += a if index >= hires else 0
            a, b = b, a + b
        quote = max(1, forecast_price(obs, "WHEAT", inventory["WHEAT"] + RIVAL_BUDGET_MARGIN) - 2)
        sold = min(shed["WHEAT"], max(0, -(-(wages - budget) // quote)))
        if sold > 0:
            orders.append(["SELL", "WHEAT", int(sold)])
            budget += sold * quote
            shed["WHEAT"] -= sold
    for _ in range(pending["hire"]["HIRE"]):
        a, b = 1, 1
        for _ in range(hires):
            a, b = b, a + b
        if budget < a or len(orders) >= 10:
            break
        orders.append(["HIRE"])
        budget -= a
        hires += 1
    own_wheat = (2 <= day <= 5 and obs["hour"] < 12 and any(
        isinstance(t, dict) and t.get("crop") == "WHEAT" and t.get("yield_units", 0) > 0 and desired.get(y * 10 + x) != "WHEAT"
        for y, row in enumerate(tiles) for x, t in enumerate(row)))
    urgent_feed = sum(isinstance(t, dict) and bool(t.get("animal")) and not t.get("fed_today")
                      and (t.get("consecutive_unfed", 0) >= 1 or day >= 1 and not own_wheat and _animal_service(t, day, day <= 5)[0])
                      and not (t["animal"] == "SHEEP" and day >= 28)
                      for row in tiles for t in row)
    urgent_feed = max(0, urgent_feed - shed.get("WHEAT", 0) - carried_feed)
    keep = _harvest_feed_keep([t for row in tiles for t in row], desired, day, obs["hour"], carried["WHEAT"])
    if keep is not None:
        urgent_feed = min(urgent_feed, keep)
    if midnight_full:
        urgent_feed = 0
    urgent_bought = 0
    while urgent_bought < min(urgent_feed, room) and len(orders) < 10:
        quote = forecast_price(obs, "WHEAT", inventory["WHEAT"] - RIVAL_BUDGET_MARGIN - urgent_bought - 1)
        if budget < quote:
            break
        budget -= quote
        urgent_bought += 1
    if urgent_bought:
        orders.append(["BUY_PRODUCT", "WHEAT", urgent_bought])
        shed["WHEAT"] = shed.get("WHEAT", 0) + urgent_bought
        inventory["WHEAT"] -= urgent_bought
        room -= urgent_bought
    if pending_land and len(orders) < 10:
        cost = (1000, 2000, 4000)[owned - 1]
        if budget >= cost + (0 if owned == 1 else 300):
            orders.append(["BUY_LAND"])
            budget -= cost
    hold = 1000 if owned == 1 and day >= 6 and not any(o[0] == "BUY_LAND" for o in orders) else 0
    budget -= hold
    def buy_animals(budget, room):
        for animal in ANIMAL_COST:
            quantity = min(pending["animal"][animal], max(0, int(budget // ANIMAL_COST[animal])), room)
            if quantity and len(orders) < 10:
                orders.append(["BUY_ANIMAL", animal, quantity])
                budget -= quantity * ANIMAL_COST[animal]
                room -= quantity
        return budget, room
    if day <= 5:
        budget, room = buy_animals(budget, room)
    plant_batch = max(1, len(farm.get("hands", [])) + 1)
    animal_reserve = min((ANIMAL_COST[a] for a in ANIMAL_COST if pending["animal"][a] > 0), default=0) if day <= 5 else 0
    for crop in sorted(CROP_COST, key=lambda c: (-CROP_COST[c], c)):
        spendable = budget - (animal_reserve if crop != "WHEAT" and (crop != "MELON" or day >= 2) else 0)
        quantity = min(pending["seed"][crop], max(0, int(spendable // CROP_COST[crop])), plant_batch)
        if quantity and len(orders) < 10:
            orders.append(["BUY_SEED", crop, quantity])
            budget -= quantity * CROP_COST[crop]
    if day == 4 and not any(pending["animal"].values()) and len(orders) < 10:
        # Today's layout is paid for: spare cash brings tomorrow's strawberries forward, farthest cells first.
        bought = {o[1]: o[2] for o in orders if o[0] == "BUY_SEED"}
        if all(pending["seed"][c] <= bought.get(c, 0) for c in CROP_COST):
            tomorrow = _opener_cells(day + 1, obs)
            flat = [t for row in tiles for t in row]
            cells = sorted((cell for cell, label in desired.items() if label == "WHEAT" and tomorrow[cell] == "STRAWBERRY"
                            and isinstance(flat[cell], dict) and flat[cell].get("crop") == "WHEAT" and flat[cell].get("yield_units", 0) > 0),
                           key=lambda cell: (-abs(cell % 10 - 4.5) - abs(cell // 10 - 4.5), cell))
            cells = cells[:int(max(0, budget) // CROP_COST["STRAWBERRY"])]
            if cells:
                state.setdefault("_advance", {}).update(dict.fromkeys(cells, "STRAWBERRY"))
                for order in orders:
                    if order[:2] == ["BUY_SEED", "STRAWBERRY"]:
                        order[2] += len(cells)
                        break
                else:
                    orders.append(["BUY_SEED", "STRAWBERRY", len(cells)])
                budget -= len(cells) * CROP_COST["STRAWBERRY"]
    if day >= 6:
        budget, room = buy_animals(budget, room)
    shortage = 0 if own_wheat or midnight_full else max(0, feed_need - shed.get("WHEAT", 0) - carried_feed)
    pending["feed"]["WHEAT"] = shortage
    # Opener: the layout comes first. Seeds still wanted are paid for before feed; feed takes
    # whatever cash is left. (Feed for an animal that already missed a day was bought above.)
    if day == 0:
        bought = {o[1]: o[2] for o in orders if o[0] == "BUY_SEED"}
        budget -= sum(max(0, pending["seed"][c] - bought.get(c, 0)) * CROP_COST[c] for c in CROP_COST)
        got = {o[1]: o[2] for o in orders if o[0] == "BUY_ANIMAL"}
        budget -= sum(max(0, pending["animal"][a] - got.get(a, 0)) * ANIMAL_COST[a] for a in ANIMAL_COST)
    quantity = 0
    while quantity < min(shortage, room) and len(orders) < 10:
        # The engine quotes BUY_PRODUCT at inventory AFTER this unit's buy.
        quote = forecast_price(obs, "WHEAT", inventory["WHEAT"] - RIVAL_BUDGET_MARGIN - quantity - 1)
        if budget < quote:
            break
        budget -= quote
        quantity += 1
    if quantity:
        orders.append(["BUY_PRODUCT", "WHEAT", quantity])
    if day == 1 and quantity >= shortage and not any(pending["animal"].values()) and len(orders) < 10:
        tomorrow = _opener_cells(2, obs)
        wanted = sum(1 for cell, label in enumerate(tomorrow) if label == "MELON" and desired.get(cell) != "MELON"
                     and not (isinstance(tiles[cell // 10][cell % 10], dict) and tiles[cell // 10][cell % 10].get("crop") == "MELON"))
        bought = sum(o[2] for o in orders if o[:2] == ["BUY_SEED", "MELON"])
        spare = seeds.get("MELON", 0) + bought - seed_target["MELON"]
        extra = min(max(0, wanted - max(0, spare)), int(max(0, budget) // CROP_COST["MELON"]))
        if extra:
            orders.append(["BUY_SEED", "MELON", extra])
    return orders

def _agent_impl(observation,configuration=None):
    player = observation['player']
    farm = observation['farms'][player]
    _NOW.clear(); _NOW.update(observation.get('market', {}).get('prices', {}))
    if len(farm['tiles'])!=10 or any(len(row)!=10 for row in farm['tiles']):
        return {'farmer':['PASS'],'hands':[['PASS'] for _ in farm['hands']],'market':[]}
    step = observation.get('step',observation['day']*24+observation['hour'])
    if step==0 or player not in _STATES or step<=_STATES[player].get('_last_step',-1):
        _STATES[player] = {'blocks':TEMPLATE['blocks'],'component':COMPONENT}
    state = _STATES[player]
    state['_last_step'] = step
    desired = _desired(observation,state)
    actions = worker_actions(observation,state,desired)
    hands = TEMPLATE['hands'][min(29,observation['day'])]
    if COMPONENT<3:
        hands = TEMPLATE['hands'][min(5,observation['day'])]
    missing = next((q for q in ('NE','SW','SE') if q not in farm['unlocked_quadrants']),None)
    land_due = COMPONENT>=3 and missing is not None and TEMPLATE['land'][missing] is not None and step>=TEMPLATE['land'][missing]
    if land_due:
        cells = [tile for row in farm['tiles'] for tile in row if tile!='LOCKED']
        used = sum(isinstance(tile,dict) and (tile.get('kind')=='PLANT' or bool(tile.get('animal'))) for tile in cells)
        land_due = used>=0.8*len(cells) or farm['money']>=3000+(1000,2000,4000)[min(2,len(farm['unlocked_quadrants'])-1)]
    orders = market_orders(observation,state,desired,hands,land_due,actions)
    if step==0:
        orders = [['BUY_ANIMAL','COW',1]]
    if missing is not None and any(order[0]=='BUY_LAND' for order in orders):
        state.setdefault('_land_offer',{})[missing] = {'day':observation['day'],'shops':list(observation['town']['unlocked_shops']),'prices':dict(observation['market']['prices'])}
    return {'farmer':actions[0],'hands':actions[1:],'market':orders}

ERRORS = {"count": 0, "last": ""}

def agent(observation, configuration=None):
    """Entry point with a safety net: on an error, keep the workers going without market orders,
    and only as a last resort pass the turn. Errors are counted in ERRORS."""
    try:
        return _agent_impl(observation, configuration)
    except Exception as error:
        ERRORS["count"] += 1
        ERRORS["last"] = repr(error)
    farm = observation['farms'][observation['player']]
    try:
        state = _STATES.setdefault(observation['player'], {'blocks': TEMPLATE['blocks'], 'component': COMPONENT})
        actions = worker_actions(observation, state, _desired(observation, state))
        return {'farmer': actions[0], 'hands': actions[1:], 'market': []}
    except Exception as error:
        ERRORS["count"] += 1
        ERRORS["last"] = repr(error)
        return {'farmer': ['PASS'], 'hands': [['PASS'] for _ in farm.get('hands', [])], 'market': []}
