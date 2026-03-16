import React, { useState, useMemo } from "react";
import {
    Tabs, Card, Text, ScrollArea, Container, Title,
    Flex, Button, TextInput, MultiSelect, Grid, Loader,
    Paper, Center, Divider, Checkbox, Group,
    rem, Modal, useMantineColorScheme
} from "@mantine/core";
import { debounce } from "lodash";
import { showNotification } from "@mantine/notifications";
import { FaCheck, FaTimes } from "react-icons/fa";

const STATIC_STUDENTS = [
    {
        id: "21BCS030",
        username: "21BCS030",
        full_name: "ARJIT PATEL",
        user_type: "student",
        programme: "B.Tech",
        discipline: "Computer Science and Engineering",
        batch: 2021,
        curr_semester_no: 8,
        category: "GEN",
        gender: "male"
    },
    {
        id: "20BEE014",
        username: "20BEE014",
        full_name: "SNEHA GUPTA",
        user_type: "student",
        programme: "B.Tech",
        discipline: "Electrical and Electronics Engineering",
        batch: 2020,
        curr_semester_no: 8,
        category: "OBC",
        gender: "female"
    },
    {
        id: "22MCS007",
        username: "22MCS007",
        full_name: "RAHUL SINGH",
        user_type: "student",
        programme: "M.Tech",
        discipline: "Computer Science and Engineering",
        batch: 2022,
        curr_semester_no: 2,
        category: "GEN",
        gender: "male"
    },
    {
        id: "21BEC021",
        username: "21BEC021",
        full_name: "PRIYA VERMA",
        user_type: "student",
        programme: "B.Tech",
        discipline: "Electronics and Communication Engineering",
        batch: 2021,
        curr_semester_no: 6,
        category: "SC",
        gender: "female"
    },
    {
        id: "19BME013",
        username: "19BME013",
        full_name: "RITESH NAIR",
        user_type: "student",
        programme: "B.Tech",
        discipline: "Mechanical Engineering",
        batch: 2019,
        curr_semester_no: 8,
        category: "ST",
        gender: "male"
    },
    {
        id: "23MEE002",
        username: "23MEE002",
        full_name: "NEHA SHARMA",
        user_type: "student",
        programme: "M.Tech",
        discipline: "Mechanical Engineering",
        batch: 2023,
        curr_semester_no: 1,
        category: "GEN",
        gender: "female"
    },
    {
        id: "21BCS019",
        username: "21BCS019",
        full_name: "ADITYA RAO",
        user_type: "student",
        programme: "B.Tech",
        discipline: "Computer Science and Engineering",
        batch: 2021,
        curr_semester_no: 6,
        category: "GEN",
        gender: "male"
    },
    {
        id: "20BCE025",
        username: "20BCE025",
        full_name: "AARUSHI MEHTA",
        user_type: "student",
        programme: "B.Tech",
        discipline: "Civil Engineering",
        batch: 2020,
        curr_semester_no: 7,
        category: "OBC",
        gender: "female"
    },
    {
        id: "22PHDCSE01",
        username: "22PHDCSE01",
        full_name: "DR. TANVI DAS",
        user_type: "student",
        programme: "PhD",
        discipline: "Computer Science and Engineering",
        batch: 2022,
        curr_semester_no: 3,
        category: "GEN",
        gender: "female"
    },
    {
        id: "21BEE017",
        username: "21BEE017",
        full_name: "KARAN THAKUR",
        user_type: "student",
        programme: "B.Tech",
        discipline: "Electrical and Electronics Engineering",
        batch: 2021,
        curr_semester_no: 5,
        category: "SC",
        gender: "male"
    }
];
const InfoCard = ({ person, selectable, selected, onSelectChange }) => {
    const { colorScheme } = useMantineColorScheme();
    const isDark = colorScheme === "dark";
    return (
        <Card shadow="sm" radius="xl" withBorder p="lg" style={{
            backgroundColor: isDark ? "#2c2e33" : "#fdfdfd",
            color: isDark ? "#fff" : "#000"
        }}>
            <Group position="apart" align="flex-start">
                <div style={{ flex: 1 }}>
                    <Text fw={600} size="lg" mb="xs" style={{ color: isDark ? "#fff" : "#000" }}>{person.full_name}</Text>
                    <Text size="sm" c="dimmed"><strong>Username:</strong> {person.username}</Text>
                    <Divider my="sm" />
                    <Text size="sm" style={{ color: isDark ? "#ccc" : "#000" }}><strong>Programme:</strong> {person.programme}</Text>
                    <Text size="sm" style={{ color: isDark ? "#ccc" : "#000" }}><strong>Discipline:</strong> {person.discipline}</Text>
                    <Text size="sm" style={{ color: isDark ? "#ccc" : "#000" }}><strong>Batch:</strong> {person.batch}</Text>
                    <Text size="sm" style={{ color: isDark ? "#ccc" : "#000" }}><strong>Semester:</strong> {person.curr_semester_no}</Text>
                    <Text size="sm" style={{ color: isDark ? "#ccc" : "#000" }}><strong>Category:</strong> {person.category}</Text>
                    <Text size="sm" style={{ color: isDark ? "#ccc" : "#000" }}><strong>Gender:</strong> {person.gender}</Text>
                </div>
                {selectable && (
                    <Checkbox
                        checked={selected}
                        onChange={() => onSelectChange(person.username)}
                        mt="sm"
                    />
                )}
            </Group>
        </Card>
    );
};

const extractUnique = (arr, key) =>
    [...new Set(arr.map((item) => key === "semester"
        ? String(item.curr_semester_no)
        : String(item[key])
    ))];

const filterAndSearch = (data, filters, searchQuery) =>
    data.filter((person) => {
        const matchSearch = person.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            person.username.toLowerCase().includes(searchQuery.toLowerCase());

        const matchFilters = Object.entries(filters).every(([key, values]) => {
            if (values.length === 0) return true;
            const value = key === "semester" ? String(person.curr_semester_no) : String(person[key]);
            return values.includes(value);
        });

        return matchSearch && matchFilters;
    });

const ArchiveStudentPage = () => {
    const checkIcon = <FaCheck style={{ width: rem(20), height: rem(20) }} />;

    const [activeTab, setActiveTab] = useState("archive");
    const [searchQuery, setSearchQuery] = useState("");
    const [filters, setFilters] = useState({
        programme: [], discipline: [], batch: [], category: [], semester: [], gender: []
    });
    const [selectedUsernames, setSelectedUsernames] = useState([]);
    const [modalOpened, setModalOpened] = useState(false);
    const [actionType, setActionType] = useState("");

    const handleSearchChange = useMemo(() =>
        debounce((value) => setSearchQuery(value), 200), []);

    const filteredData = useMemo(() =>
        filterAndSearch(STATIC_STUDENTS, filters, searchQuery),
        [filters, searchQuery]
    );

    const isSelected = (username) => selectedUsernames.includes(username);
    const toggleSelect = (username) => {
        setSelectedUsernames((prev) =>
            prev.includes(username) ? prev.filter(u => u !== username) : [...prev, username]
        );
    };

    const selectAll = () => {
        setSelectedUsernames(filteredData.map(u => u.username));
    };

    const clearSelection = () => setSelectedUsernames([]);

    const handleAction = (type) => {
        setActionType(type);
        setModalOpened(true);
    };

    const confirmAction = () => {
        showNotification({
            icon: checkIcon,
            title: "Success",
            position: "top-center",
            withCloseButton: true,
            autoClose: 5000,
            message: `Marked selected students as "${actionType}"`,
            color: "green",
        });
        clearSelection();
        setModalOpened(false);
    };

    return (
        <Container size="lg" py="xl">
            <Flex
                direction={{ base: 'column', sm: 'row' }}
                gap={{ base: 'sm', sm: 'lg' }}
                justify={{ sm: 'center' }}
                mb="xl"
            >
                <Button
                    variant="gradient"
                    size="xl"
                    radius="xs"
                    gradient={{ from: 'blue', to: 'cyan', deg: 90 }}
                    sx={{ display: 'block', width: { base: '100%', sm: 'auto' }, whiteSpace: 'normal', padding: '1rem', textAlign: 'center' }}
                >
                    <Title order={1} sx={{ fontSize: { base: 'lg', sm: 'xl' }, lineHeight: 1.2, wordBreak: 'break-word' }}>
                        Archive Students
                    </Title>
                </Button>
            </Flex>

            <Paper shadow="lg" p="xl" radius="xl" withBorder>
                <Tabs value={activeTab} onChange={setActiveTab} variant="pills" color="blue" radius="lg" keepMounted={false}>
                    <Tabs.List grow mb="lg">
                        <Tabs.Tab value="archive">ARCHIVE</Tabs.Tab>
                        <Tabs.Tab value="archived">ARCHIVED</Tabs.Tab>
                        <Tabs.Tab value="alumnis">ALUMNIS</Tabs.Tab>
                    </Tabs.List>

                    <Tabs.Panel value="archive">
                        <Grid mb="lg">
                            <Grid.Col span={12}>
                                <TextInput
                                    placeholder="🔍 Search students"
                                    radius="md"
                                    onChange={(e) => handleSearchChange(e.currentTarget.value)}
                                />
                            </Grid.Col>
                            {["programme", "discipline", "batch", "semester", "category", "gender"].map((key) => (
                                <Grid.Col span={6} key={key}>
                                    <MultiSelect
                                        label={key[0].toUpperCase() + key.slice(1)}
                                        placeholder={`Filter by ${key}`}
                                        value={filters[key]}
                                        onChange={(value) => setFilters((prev) => ({ ...prev, [key]: value }))}
                                        data={extractUnique(STATIC_STUDENTS, key)}
                                        radius="md"
                                        searchable
                                        clearable
                                    />
                                </Grid.Col>
                            ))}
                        </Grid>

                        <Group mb="md">
                            <Button onClick={selectAll} variant="light">Select All</Button>
                            <Button onClick={clearSelection} variant="default">Clear Selection</Button>
                        </Group>

                        <ScrollArea h={400}>
                            <Grid>
                                {filteredData.map((student) => (
                                    <Grid.Col span={12} key={student.username}>
                                        <InfoCard
                                            person={student}
                                            selectable
                                            selected={isSelected(student.username)}
                                            onSelectChange={toggleSelect}
                                        />
                                    </Grid.Col>
                                ))}
                            </Grid>
                        </ScrollArea>

                        {selectedUsernames.length > 0 && (
                            <Group mt="lg" position="right">
                                <Button color="blue" onClick={() => handleAction("archived")}>Archive</Button>
                                <Button color="teal" onClick={() => handleAction("alumni")}>Alumni</Button>
                            </Group>
                        )}
                    </Tabs.Panel>

                    <Tabs.Panel value="archived">
                        <Title order={3} mb="md">Recently Archived</Title>
                        <Grid>
                            {STATIC_STUDENTS.slice(0, 2).map((s) => (
                                <Grid.Col span={12} key={s.username}>
                                    <InfoCard person={s} />
                                </Grid.Col>
                            ))}
                        </Grid>
                    </Tabs.Panel>

                    <Tabs.Panel value="alumnis">
                        <Title order={3} mb="md">Recent Alumnis</Title>
                        <Grid>
                            {STATIC_STUDENTS.slice(2, 4).map((s) => (
                                <Grid.Col span={12} key={s.username}>
                                    <InfoCard person={s} />
                                </Grid.Col>
                            ))}
                        </Grid>
                    </Tabs.Panel>
                </Tabs>
            </Paper>

            <Modal
                opened={modalOpened}
                onClose={() => setModalOpened(false)}
                title={`Confirm Marking as ${actionType.toUpperCase()}`}
            >
                <Text size="sm">Are you sure you want to mark the selected students as {actionType}?</Text>
                <Group mt="md" position="right">
                    <Button variant="light" onClick={() => setModalOpened(false)}>Cancel</Button>
                    <Button color="blue" onClick={confirmAction}>Confirm</Button>
                </Group>
            </Modal>
        </Container>
    );
};

export default ArchiveStudentPage;