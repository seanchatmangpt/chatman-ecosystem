def observe(rows):
 d={r['result_digest'] for r in rows}
 return {"sensor":"result_correspondence","digests":sorted(d),"standing":"ALIVE" if len(d)==1 else "BUILD_BROKEN[RESULT_DIVERGENCE]"}
