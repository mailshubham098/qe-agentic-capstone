package com.ibm.qe.tests;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Skeleton smoke test -- proves the Maven compile + Surefire cycle is healthy.
 * This test has no runtime dependency on any application under test and must
 * always pass green on the CI runner.
 *
 * Real test cases (QEC-T301 to QEC-T317) will be added per workflow as the
 * agentic QE workflows (WF04, WF06, WF07) are executed.
 */
class SmokeTest {

    @Test
    @DisplayName("tc301_pipelineSmokePassesWithNoApplicationDependency")
    void tc301_pipelineSmokePassesWithNoApplicationDependency() {
        // Validates that the Java 21 + JUnit 5 + AssertJ stack compiles and runs.
        assertThat(System.getProperty("java.version"))
                .as("Java version must be 21 or higher")
                .isNotNull();

        assertThat(Runtime.version().feature())
                .as("Java feature release must be >= 21")
                .isGreaterThanOrEqualTo(21);
    }
}
