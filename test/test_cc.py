
"test cc module with py.test."

import cc

def test_clone_review_for_junit_sql():
    "Test if a changeset contains a sql file used in Junit."
    co_files_text = """/vob/visionway/ctm/common/dbmodel/src/test/resources/user_test_db.sql
/vob/visionway/ctm/common/dbmodel/src/test/resources/cpo_fault_test_db.sql
/vob/visionway/ctm/common/dbmodel/src/main/java/com/cisco/nm/ctm/dbmodel/fault/FaultRepository.java
/vob/visionway/ctm/common/dbmodel/src/test/java/com/cisco/nm/ctm/dbmodel/fault/AlarmTest.java
/vob/visionway/ctm/common/dbmodel/src/main/java/com/cisco/nm/ctm/dbmodel/fault/WritableAlarmEntity.java
/vob/visionway/ctm/common/platform/src/main/java/com/cisco/stardm/platform/fault/AlarmCounters.java"""
    co_files = co_files_text.split('\n')
    cs = cc.ChangeSet(co_files)
    assert len(cs.filterForSql()) == 0

def test_clone_review_for_sql():
    "Test if a changeset contains a sql file not used in Junit."
    co_files_text = """/vob/visionway/ctm/server/install/vws/ctm_base_tables.sql
/vob/visionway/ctm/common/dbmodel/src/main/java/com/cisco/nm/ctm/dbmodel/fault/FaultRepository.java
/vob/visionway/ctm/common/dbmodel/src/test/java/com/cisco/nm/ctm/dbmodel/fault/AlarmTest.java
/vob/visionway/ctm/common/dbmodel/src/main/java/com/cisco/nm/ctm/dbmodel/fault/WritableAlarmEntity.java
/vob/visionway/ctm/common/platform/src/main/java/com/cisco/stardm/platform/fault/AlarmCounters.java"""
    co_files = co_files_text.split('\n')
    cs = cc.ChangeSet(co_files)
    assert len(cs.filterForSql()) == 1

