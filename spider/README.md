docs for spider classes
=========================

##MRLManager##
方法:

1. *el_requests(url,\*\*kwargs)*: 在确保登录的情况下下载一个文件

使用:

MRLRequest(帐号列表, 访问类名)  
访问类名必须为*MultiRequestsWithLogin*的子类

##MultiRequestsWithLogin##
方法:

1. set_nologin: 在内容获取失败时标识为已经丢失登录状态  
2. do_login: 确保登录

子类必须实现的方法:

1. _real_do_login: 具体的登录动作  
2. need_login(url,response): 从url和回应来检测是否需要登录


##Spider##
拉取数据的核心类,由子类继承后再使用

方法:

1. add_job(job, is_main_job)
    分两种任务: 主任务放进有限队列,先进先出, 次任务放入无限队列,后进先出
    job本身可以是任何对象,但None表示不再有任务了
2. wait_q() 一般在dispatch中使用,等待所有任务结束

使用说明:

    a = SubSpider(线程数量)
    a.load_proxy('proxy_file') #可选,加载代理列表.
    a.run()

子类需实现的接口:

1. dispatch: 分发任务, 用None任务表示所有任务结束
2. run_job(job) 执行job.


##GenQueries##
查询器细化,这是Spider的子类

子类必须实现的接口:

1. init_conditions()
    初使化条件. 一般可用GQDataHelper.add(self, keyname, value) 来添加一种条件
    value可以是list或dict形式.
    list如: [['M', '男'], ['F', '女']]   list[i][0]被使用, list[i][1:]不用,为代码文档
    dict如:
    
        {
            k1:{ desc:'说明男', 'value':'M',
                children:{
                    k1:{value:'GM', desc:'好男'}, k2:{value:'BM'}
                }
            },
            k2:{value:'F'}
        }
    dict形式下的子条件会被再一次细分.  
    另外还需要设计初始url和名字, 如:
    
        self.name = 'lp_queries'
        self.baseurl = {}
    baseurl可以设置为一个空的dict或者是一个字符串. 细化时条件会加到dict中,或者是直接合并到字符串中形成最终url.
2. need_split(url, level, is_last)  
    url是dict或子符串,视baseurl格式而定,推荐使用dict,这样更方便运算.对于简单任务用字符串,方便.  
    level表示细化条件的级别.  
    is_last表示是不是细化到最后一级了.

    在need_split中也可以再调用add_job添加任务,然后实现run_job运行这些再细化的任务.记得要调用父类GenQueries.run_job方法
3. process_failed_url(url)
    可选实现, 处理最后一层还是细化失败的条件.


##spider.util##
1. sendmail('lixungeng@ipin.com', '这是标题', '这是正文')
2. chained_regex
    用几个regex来先后处理文件, ()内的内容作为下一级的输入
3. unique_list:
    确保list内的重复内容被删掉
